#!/usr/bin/env python3
"""
Cookie Clicker Game - Python FastAPI Backend with DynamoDB
メインアプリケーションファイル
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Optional
from decimal import Decimal

import uvicorn
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# アプリケーション作成
app = FastAPI(
    title="Cookie Clicker API",
    description="Cookie Clicker Game Backend API with DynamoDB",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では制限する
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================================================================
# 新規追加: CPS計算用ヘルパー関数
# ==============================================================================

from datetime import datetime
import time

def get_current_timestamp() -> float:
    """現在のタイムスタンプ（秒）を取得"""
    return time.time()

def calculate_current_cookies(game_data: GameData) -> int:
    """
    CPS（Cookies Per Second）を考慮した現在のクッキー数を計算
    """
    saved_cookies = game_data.cookies
    last_update = getattr(game_data, 'last_cps_update', None)
    cps = game_data.cookies_per_second
    
    if last_update is None or cps <= 0:
        return saved_cookies
    
    # 前回更新からの経過時間を計算（秒）
    current_time = get_current_timestamp()
    
    # last_updateが文字列の場合はfloatに変換
    if isinstance(last_update, str):
        try:
            last_update = float(last_update)
        except ValueError:
            # 変換できない場合は現在時刻を使用
            last_update = current_time
    
    elapsed_seconds = max(0, current_time - last_update)
    
    # CPS分のクッキーを追加
    generated_cookies = int(elapsed_seconds * cps)
    current_cookies = saved_cookies + generated_cookies
    
    logger.info(f"🍪 CPS計算: saved={saved_cookies}, elapsed={elapsed_seconds:.1f}s, cps={cps}, generated={generated_cookies}, total={current_cookies}")
    
    return current_cookies

def update_game_data_with_cps(game_data: GameData) -> GameData:
    """
    CPS考慮でゲームデータを最新状態に更新
    """
    current_cookies = calculate_current_cookies(game_data)
    
    # ゲームデータを更新
    game_data.cookies = current_cookies
    game_data.last_cps_update = get_current_timestamp()
    
    return game_data


# ==============================================================================
# DynamoDB設定
# ==============================================================================

# DynamoDB接続設定
DYNAMODB_ENDPOINT = os.getenv("DYNAMODB_ENDPOINT", "http://localhost:8000")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

# DynamoDBクライアント作成
dynamodb = boto3.resource(
    'dynamodb',
    endpoint_url=DYNAMODB_ENDPOINT,
    region_name=AWS_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "dummy"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "dummy")
)

# テーブル名
GAME_DATA_TABLE = "cookie_clicker_game_data"
UPGRADES_TABLE = "cookie_clicker_upgrades"
ACHIEVEMENTS_TABLE = "cookie_clicker_achievements"

# ==============================================================================
# データモデル
# ==============================================================================

class GameData(BaseModel):
    """ゲームデータモデル"""
    user_id: str
    cookies: int = Field(default=0, ge=0)
    cookies_per_second: int = Field(default=0, ge=0)
    click_power: int = Field(default=1, ge=1)
    upgrades: Dict[str, int] = Field(default_factory=dict)
    total_clicks: int = Field(default=0, ge=0)
    last_cps_update: Optional[float] = None  # 🔥 CPS更新用タイムスタンプ追加
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class UpgradeItem(BaseModel):
    """アップグレードアイテムモデル"""
    id: str
    name: str
    description: str
    base_cost: int = Field(ge=1)
    current_cost: int = Field(ge=1)
    cps_boost: int = Field(default=0, ge=0)
    click_boost: int = Field(default=0, ge=0)
    owned: int = Field(default=0, ge=0)
    cost_multiplier: float = Field(default=1.15, gt=1.0)

class ClickRequest(BaseModel):
    """クリックリクエストモデル"""
    click_power: int = Field(default=1, ge=1)

class UpgradeRequest(BaseModel):
    """アップグレード購入リクエストモデル"""
    upgrade_id: str

class SaveGameRequest(BaseModel):
    """ゲーム保存リクエストモデル"""
    game_data: GameData

# ==============================================================================
# DynamoDBヘルパー関数
# ==============================================================================

def decimal_to_int(obj):
    """DynamoDBのDecimalを整数に変換"""
    if isinstance(obj, Decimal):
        return int(obj)
    return obj

def dict_decimal_to_int(data):
    """辞書内のDecimalを再帰的に整数に変換"""
    if isinstance(data, dict):
        return {k: dict_decimal_to_int(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [dict_decimal_to_int(item) for item in data]
    elif isinstance(data, Decimal):
        return int(data)
    return data

async def create_tables_if_not_exists():
    """テーブルが存在しない場合は作成"""
    try:
        # ゲームデータテーブル
        try:
            table = dynamodb.Table(GAME_DATA_TABLE)
            table.load()
            logger.info(f"Table {GAME_DATA_TABLE} already exists")
        except ClientError:
            table = dynamodb.create_table(
                TableName=GAME_DATA_TABLE,
                KeySchema=[
                    {
                        'AttributeName': 'user_id',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'user_id',
                        'AttributeType': 'S'
                    }
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            table.wait_until_exists()
            logger.info(f"Created table {GAME_DATA_TABLE}")

        # アップグレードテーブル
        try:
            upgrades_table = dynamodb.Table(UPGRADES_TABLE)
            upgrades_table.load()
            logger.info(f"Table {UPGRADES_TABLE} already exists")
        except ClientError:
            upgrades_table = dynamodb.create_table(
                TableName=UPGRADES_TABLE,
                KeySchema=[
                    {
                        'AttributeName': 'upgrade_id',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'upgrade_id',
                        'AttributeType': 'S'
                    }
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            upgrades_table.wait_until_exists()
            logger.info(f"Created table {UPGRADES_TABLE}")
            
            # 初期データを挿入
            await populate_initial_data()

    except Exception as e:
        logger.error(f"Error creating tables: {str(e)}")

async def populate_initial_data():
    """初期データをDynamoDBに挿入"""
    upgrades_table = dynamodb.Table(UPGRADES_TABLE)
    
    initial_upgrades = [
        {
            "upgrade_id": "cursor",
            "name": "Cursor",
            "description": "Clicks cookies for you automatically",
            "base_cost": 15,
            "cps_boost": 1,
            "click_boost": 0,
            "cost_multiplier": Decimal("1.15")
        },
        {
            "upgrade_id": "grandma",
            "name": "Grandma",
            "description": "A nice grandma to bake more cookies",
            "base_cost": 100,
            "cps_boost": 5,
            "click_boost": 0,
            "cost_multiplier": Decimal("1.15")
        },
        {
            "upgrade_id": "farm",
            "name": "Cookie Farm",
            "description": "Grows cookie plants!",
            "base_cost": 1100,
            "cps_boost": 47,
            "click_boost": 0,
            "cost_multiplier": Decimal("1.15")
        },
        {
            "upgrade_id": "mine",
            "name": "Cookie Mine",
            "description": "Mines cookie ore from deep underground",
            "base_cost": 12000,
            "cps_boost": 260,
            "click_boost": 0,
            "cost_multiplier": Decimal("1.15")
        },
        {
            "upgrade_id": "factory",
            "name": "Cookie Factory",
            "description": "Mass-produces cookies",
            "base_cost": 130000,
            "cps_boost": 1400,
            "click_boost": 0,
            "cost_multiplier": Decimal("1.15")
        },
        {
            "upgrade_id": "click_power",
            "name": "Better Clicks",
            "description": "Each click gives more cookies",
            "base_cost": 50,
            "cps_boost": 0,
            "click_boost": 1,
            "cost_multiplier": Decimal("1.15")
        },
        {
            "upgrade_id": "super_clicks",
            "name": "Super Clicks",
            "description": "Greatly enhances clicking power",
            "base_cost": 500,
            "cps_boost": 0,
            "click_boost": 5,
            "cost_multiplier": Decimal("1.15")
        }
    ]
    
    for upgrade in initial_upgrades:
        try:
            upgrades_table.put_item(Item=upgrade)
        except Exception as e:
            logger.error(f"Error inserting upgrade {upgrade['upgrade_id']}: {str(e)}")
    
    logger.info("Initial upgrade data populated")

# ==============================================================================
# ヘルパー関数
# ==============================================================================

def get_user_game_data(user_id: str) -> GameData:
    """ユーザーのゲームデータを取得（CPS考慮）"""
    table = dynamodb.Table(GAME_DATA_TABLE)
    
    try:
        response = table.get_item(Key={'user_id': user_id})
        
        if 'Item' in response:
            item = dict_decimal_to_int(response['Item'])
            game_data = GameData(**item)
            
            # 🔥 CPS考慮で現在のクッキー数を計算
            game_data = update_game_data_with_cps(game_data)
            
            return game_data
        else:
            # 新しいユーザーの場合、デフォルトデータを作成
            now = datetime.now().isoformat()
            current_timestamp = get_current_timestamp()
            
            game_data = GameData(
                user_id=user_id,
                last_cps_update=current_timestamp,  # 🔥 CPS更新タイムスタンプ設定
                created_at=now,
                updated_at=now
            )
            
            # DynamoDBに保存
            table.put_item(Item={
                **game_data.dict(),
                'created_at': now,
                'updated_at': now
            })
            
            logger.info(f"Created new game data for user: {user_id}")
            return game_data
            
    except Exception as e:
        logger.error(f"Error getting game data for {user_id}: {str(e)}")
        # エラー時はデフォルトデータを返す
        game_data = GameData(user_id=user_id)
        game_data.last_cps_update = get_current_timestamp()
        return game_data

def save_user_game_data(game_data: GameData):
    """ユーザーのゲームデータを保存（CPS更新タイムスタンプ付き）"""
    table = dynamodb.Table(GAME_DATA_TABLE)
    
    try:
        now = datetime.now().isoformat()
        
        # CPS更新タイムスタンプが未設定の場合は設定
        if game_data.last_cps_update is None:
            game_data.last_cps_update = get_current_timestamp()
        
        game_data.updated_at = now
        
        table.put_item(Item={
            **game_data.dict(),
            'updated_at': now
        })
        
    except Exception as e:
        logger.error(f"Error saving game data for {game_data.user_id}: {str(e)}")
        raise

def calculate_upgrade_cost(base_cost: int, owned_count: int, multiplier: float = 1.15) -> int:
    """アップグレードの現在のコストを計算"""
    return int(base_cost * (multiplier ** owned_count))

def get_user_upgrades(user_id: str) -> List[UpgradeItem]:
    """ユーザーのアップグレード状況を取得"""
    game_data = get_user_game_data(user_id)
    upgrades_table = dynamodb.Table(UPGRADES_TABLE)
    
    try:
        response = upgrades_table.scan()
        upgrades = []
        
        for item in response['Items']:
            item = dict_decimal_to_int(item)
            upgrade_id = item['upgrade_id']
            owned_count = game_data.upgrades.get(upgrade_id, 0)
            current_cost = calculate_upgrade_cost(
                item['base_cost'], 
                owned_count, 
                float(item['cost_multiplier'])
            )
            
            upgrade = UpgradeItem(
                id=upgrade_id,
                name=item['name'],
                description=item['description'],
                base_cost=item['base_cost'],
                current_cost=current_cost,
                cps_boost=item['cps_boost'],
                click_boost=item['click_boost'],
                owned=owned_count,
                cost_multiplier=float(item['cost_multiplier'])
            )
            upgrades.append(upgrade)
        
        return upgrades
        
    except Exception as e:
        logger.error(f"Error getting upgrades for {user_id}: {str(e)}")
        return []

def calculate_total_cps(game_data: GameData) -> int:
    """合計CPS（Cookies Per Second）を計算"""
    upgrades_table = dynamodb.Table(UPGRADES_TABLE)
    total_cps = 0
    
    try:
        for upgrade_id, owned_count in game_data.upgrades.items():
            if owned_count > 0:
                response = upgrades_table.get_item(Key={'upgrade_id': upgrade_id})
                if 'Item' in response:
                    item = dict_decimal_to_int(response['Item'])
                    total_cps += item['cps_boost'] * owned_count
    except Exception as e:
        logger.error(f"Error calculating CPS: {str(e)}")
    
    return total_cps

def calculate_total_click_power(game_data: GameData) -> int:
    """合計クリックパワーを計算"""
    upgrades_table = dynamodb.Table(UPGRADES_TABLE)
    total_power = 1  # 基本クリックパワー
    
    try:
        for upgrade_id, owned_count in game_data.upgrades.items():
            if owned_count > 0:
                response = upgrades_table.get_item(Key={'upgrade_id': upgrade_id})
                if 'Item' in response:
                    item = dict_decimal_to_int(response['Item'])
                    total_power += item['click_boost'] * owned_count
    except Exception as e:
        logger.error(f"Error calculating click power: {str(e)}")
    
    return total_power

# ==============================================================================
# イベントハンドラー
# ==============================================================================

@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の処理"""
    logger.info("Starting Cookie Clicker API with DynamoDB")
    await create_tables_if_not_exists()
    logger.info("DynamoDB tables ready")

# ==============================================================================
# API エンドポイント
# ==============================================================================

@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "Cookie Clicker API with DynamoDB",
        "version": "1.0.0",
        "status": "running",
        "database": "DynamoDB",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {
        "status": "healthy",
        "database": "DynamoDB",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/game/{user_id}")
async def get_game_data(user_id: str):
    """ゲームデータ取得（CPS考慮の最新クッキー数）"""
    try:
        # 🔥 CPS考慮でゲームデータを取得
        game_data = get_user_game_data(user_id)
        upgrades = get_user_upgrades(user_id)
        
        # CPS とクリックパワーを再計算
        game_data.cookies_per_second = calculate_total_cps(game_data)
        game_data.click_power = calculate_total_click_power(game_data)
        
        # 🔥 CPS考慮でクッキー数を再計算（最新状態に更新）
        game_data = update_game_data_with_cps(game_data)
        
        # 更新されたデータを保存
        save_user_game_data(game_data)
        
        logger.info(f"Retrieved game data for user: {user_id} (cookies: {game_data.cookies}, cps: {game_data.cookies_per_second})")
        
        return {
            "game_data": game_data.dict(),
            "upgrades": [upgrade.dict() for upgrade in upgrades],
            "message": "Game data retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving game data for {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve game data")

@app.post("/api/v1/game/{user_id}/click")
async def handle_click(user_id: str, request: ClickRequest):
    """クリック処理（CPS考慮）"""
    try:
        # 🔥 CPS考慮でゲームデータを取得
        game_data = get_user_game_data(user_id)
        
        # クリックパワーを再計算
        actual_click_power = calculate_total_click_power(game_data)
        
        # 🔥 クッキーを追加（CPS分は既に加算済み）
        cookies_earned = actual_click_power
        game_data.cookies += cookies_earned
        game_data.total_clicks += 1
        
        # 🔥 CPS更新タイムスタンプを現在時刻に設定
        game_data.last_cps_update = get_current_timestamp()
        
        # DynamoDBに保存
        save_user_game_data(game_data)
        
        logger.info(f"User {user_id} clicked: +{cookies_earned} cookies (total: {game_data.cookies})")
        
        return {
            "user_id": user_id,
            "cookies_earned": cookies_earned,
            "total_cookies": game_data.cookies,
            "cookies_per_second": game_data.cookies_per_second,
            "click_power": actual_click_power,
            "total_clicks": game_data.total_clicks,
            "message": "Click processed successfully"
        }
        
    except Exception as e:
        logger.error(f"Error processing click for {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process click")

@app.post("/api/v1/game/{user_id}/upgrade")
async def purchase_upgrade(user_id: str, request: UpgradeRequest):
    """アップグレード購入処理（CPS考慮）"""
    try:
        # 🔥 CPS考慮でゲームデータを取得
        game_data = get_user_game_data(user_id)
        upgrade_id = request.upgrade_id
        
        # アップグレード情報を取得
        upgrades_table = dynamodb.Table(UPGRADES_TABLE)
        response = upgrades_table.get_item(Key={'upgrade_id': upgrade_id})
        
        if 'Item' not in response:
            raise HTTPException(status_code=404, detail="Upgrade not found")
        
        upgrade_info = dict_decimal_to_int(response['Item'])
        
        # 現在の所有数とコストを計算
        owned_count = game_data.upgrades.get(upgrade_id, 0)
        cost = calculate_upgrade_cost(
            upgrade_info['base_cost'], 
            owned_count, 
            float(upgrade_info['cost_multiplier'])
        )
        
        # 🔥 クッキーが足りるかチェック（CPS分も含んだ正確な値）
        current_cookies = game_data.cookies  # CPS考慮済み
        if current_cookies < cost:
            return {
                "user_id": user_id,
                "upgrade_id": upgrade_id,
                "success": False,
                "message": f"Not enough cookies. Need {cost}, have {current_cookies}",
                "cost": cost,
                "current_cookies": current_cookies
            }
        
        # アップグレードを購入
        game_data.cookies -= cost
        game_data.upgrades[upgrade_id] = owned_count + 1
        
        # CPS とクリックパワーを再計算
        game_data.cookies_per_second = calculate_total_cps(game_data)
        game_data.click_power = calculate_total_click_power(game_data)
        
        # 🔥 CPS更新タイムスタンプを現在時刻に設定
        game_data.last_cps_update = get_current_timestamp()
        
        # DynamoDBに保存
        save_user_game_data(game_data)
        
        upgrade_name = upgrade_info['name']
        logger.info(f"User {user_id} purchased {upgrade_name} for {cost} cookies (remaining: {game_data.cookies})")
        
        return {
            "user_id": user_id,
            "upgrade_id": upgrade_id,
            "upgrade_name": upgrade_name,
            "success": True,
            "cost": cost,
            "owned_count": game_data.upgrades[upgrade_id],
            "remaining_cookies": game_data.cookies,
            "new_cps": game_data.cookies_per_second,
            "new_click_power": game_data.click_power,
            "message": f"Successfully purchased {upgrade_name}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error purchasing upgrade for {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to purchase upgrade")

# 🔥 新規追加: CPS同期エンドポイント
@app.post("/api/v1/game/{user_id}/sync")
async def sync_cps(user_id: str):
    """CPS同期処理（フロントエンド用）"""
    try:
        # CPS考慮でゲームデータを取得・更新
        game_data = get_user_game_data(user_id)
        
        # 最新状態で保存
        save_user_game_data(game_data)
        
        return {
            "user_id": user_id,
            "total_cookies": game_data.cookies,
            "cookies_per_second": game_data.cookies_per_second,
            "last_update": game_data.last_cps_update,
            "message": "CPS synchronized successfully"
        }
        
    except Exception as e:
        logger.error(f"Error syncing CPS for {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to sync CPS")

@app.get("/api/v1/game/{user_id}/save")
async def save_game_simple(user_id: str):
    """簡単なゲーム保存処理（GET版）"""
    try:
        game_data = get_user_game_data(user_id)
        save_user_game_data(game_data)
        
        logger.info(f"Game auto-saved for user: {user_id}")
        
        return {
            "user_id": user_id,
            "saved_at": game_data.updated_at,
            "message": "Game auto-saved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error auto-saving game for {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to auto-save game")

@app.get("/api/v1/stats")
async def get_global_stats():
    """グローバル統計情報取得"""
    try:
        table = dynamodb.Table(GAME_DATA_TABLE)
        response = table.scan()
        
        total_users = len(response['Items'])
        total_cookies = 0
        total_clicks = 0
        
        for item in response['Items']:
            item = dict_decimal_to_int(item)
            total_cookies += item.get('cookies', 0)
            total_clicks += item.get('total_clicks', 0)
        
        return {
            "total_users": total_users,
            "total_cookies": total_cookies,
            "total_clicks": total_clicks,
            "message": "Global stats retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving global stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve global stats")

@app.get("/api/v1/leaderboard")
async def get_leaderboard(limit: int = 10):
    """リーダーボード取得"""
    try:
        table = dynamodb.Table(GAME_DATA_TABLE)
        response = table.scan()
        
        # クッキー数でソート
        items = [dict_decimal_to_int(item) for item in response['Items']]
        sorted_users = sorted(items, key=lambda x: x.get('cookies', 0), reverse=True)
        
        leaderboard = []
        for rank, user_data in enumerate(sorted_users[:limit], 1):
            leaderboard.append({
                "rank": rank,
                "user_id": user_data['user_id'],
                "cookies": user_data.get('cookies', 0),
                "cookies_per_second": user_data.get('cookies_per_second', 0),
                "total_clicks": user_data.get('total_clicks', 0)
            })
        
        return {
            "leaderboard": leaderboard,
            "total_players": len(items),
            "message": "Leaderboard retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving leaderboard: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve leaderboard")

# ==============================================================================
# アプリケーション起動
# ==============================================================================

if __name__ == "__main__":
    # 環境変数から設定を取得
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8001"))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    logger.info(f"Starting Cookie Clicker API on {host}:{port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"DynamoDB endpoint: {DYNAMODB_ENDPOINT}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if debug else "warning"
    )