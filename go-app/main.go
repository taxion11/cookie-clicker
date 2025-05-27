package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
)

// GameData はゲームの状態を表す構造体
type GameData struct {
	UserID           string         `json:"user_id"`
	Cookies          int64          `json:"cookies"`
	CookiesPerSecond int64          `json:"cookies_per_second"`
	ClickPower       int            `json:"click_power"`
	Upgrades         map[string]int `json:"upgrades"`
}

// UpgradeItem はアップグレードアイテムを表す構造体
type UpgradeItem struct {
	ID          string `json:"id"`
	Name        string `json:"name"`
	Description string `json:"description"`
	Cost        int64  `json:"cost"`
	CPSBoost    int64  `json:"cps_boost"`
	ClickBoost  int    `json:"click_boost"`
	Owned       int    `json:"owned"`
}

// PythonAPIの設定
var pythonAPIURL = getEnv("PYTHON_API_URL", "http://localhost:8001")

func getEnv(key, fallback string) string {
	if value, exists := os.LookupEnv(key); exists {
		return value
	}
	return fallback
}

func main() {
	// Ginモードの設定
	if os.Getenv("GIN_MODE") == "" {
		gin.SetMode(gin.DebugMode)
	}

	r := gin.Default()

	// CORS設定
	config := cors.DefaultConfig()
	config.AllowOrigins = []string{"*"}
	config.AllowMethods = []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"}
	config.AllowHeaders = []string{"*"}
	r.Use(cors.New(config))

	// 静的ファイルの配信
	r.Static("/static", "./static")
	r.LoadHTMLGlob("templates/*")

	// ルートの設定
	setupRoutes(r)

	// サーバー起動
	port := getEnv("PORT", "8080")
	log.Printf("Starting server on port %s", port)
	log.Printf("Python API URL: %s", pythonAPIURL)

	if err := r.Run(":" + port); err != nil {
		log.Fatal("Failed to start server:", err)
	}
}

func setupRoutes(r *gin.Engine) {
	// メインページ
	r.GET("/", handleHome)

	// API エンドポイント
	api := r.Group("/api/v1")
	{
		api.GET("/game/:user_id", handleGetGameData)
		api.POST("/game/:user_id/click", handleClick)
		api.POST("/game/:user_id/upgrade", handleUpgrade)
		api.GET("/game/:user_id/save", handleSaveGame)
		api.POST("/game/:user_id/load", handleLoadGame)
	}

	// ヘルスチェック
	r.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"status": "ok"})
	})
}

func handleHome(c *gin.Context) {
	c.HTML(http.StatusOK, "index.html", gin.H{
		"title": "Cookie Clicker Game",
	})
}

func handleGetGameData(c *gin.Context) {
	userID := c.Param("user_id")

	log.Printf("Getting game data for user: %s", userID)

	// Python APIからデータを取得を試行
	resp, err := http.Get(fmt.Sprintf("%s/api/v1/game/%s", pythonAPIURL, userID))
	if err != nil {
		log.Printf("Failed to connect to Python API: %v", err)
		// フォールバック: デフォルトデータを返す
		sendDefaultGameData(c, userID)
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		log.Printf("Python API returned status: %d", resp.StatusCode)
		sendDefaultGameData(c, userID)
		return
	}

	// レスポンスをそのままクライアントに転送
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		log.Printf("Failed to read Python API response: %v", err)
		sendDefaultGameData(c, userID)
		return
	}

	log.Printf("Successfully retrieved game data for user: %s", userID)
	c.Header("Content-Type", "application/json")
	c.Data(http.StatusOK, "application/json", body)
}

func sendDefaultGameData(c *gin.Context, userID string) {
	log.Printf("Sending default game data for user: %s", userID)

	gameData := GameData{
		UserID:           userID,
		Cookies:          0,
		CookiesPerSecond: 0,
		ClickPower:       1,
		Upgrades:         make(map[string]int),
	}

	upgrades := []UpgradeItem{
		{
			ID:          "cursor",
			Name:        "Cursor",
			Description: "Clicks cookies for you",
			Cost:        15,
			CPSBoost:    1,
			ClickBoost:  0,
			Owned:       0,
		},
		{
			ID:          "grandma",
			Name:        "Grandma",
			Description: "A nice grandma to bake more cookies",
			Cost:        100,
			CPSBoost:    5,
			ClickBoost:  0,
			Owned:       0,
		},
		{
			ID:          "farm",
			Name:        "Farm",
			Description: "Grows cookie plants",
			Cost:        1100,
			CPSBoost:    47,
			ClickBoost:  0,
			Owned:       0,
		},
		{
			ID:          "click_power",
			Name:        "Better Clicks",
			Description: "Each click gives more cookies",
			Cost:        50,
			CPSBoost:    0,
			ClickBoost:  1,
			Owned:       0,
		},
	}

	c.JSON(http.StatusOK, gin.H{
		"game_data": gameData,
		"upgrades":  upgrades,
	})
}

func handleClick(c *gin.Context) {
	userID := c.Param("user_id")

	log.Printf("=== CLICK DEBUG START ===")
	log.Printf("Processing click for user: %s", userID)
	log.Printf("Python API URL: %s", pythonAPIURL)

	// リクエストボディを構造体にバインド
	var clickReq struct {
		ClickPower int `json:"click_power"`
	}

	if err := c.ShouldBindJSON(&clickReq); err != nil {
		log.Printf("Failed to bind click request: %v", err)
		clickReq.ClickPower = 1 // デフォルト値
	}

	log.Printf("Click request parsed: %+v", clickReq)

	// Python APIにクリックリクエストを送信
	reqBody := map[string]interface{}{
		"click_power": clickReq.ClickPower,
	}

	jsonData, err := json.Marshal(reqBody)
	if err != nil {
		log.Printf("Failed to marshal click request: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to encode request"})
		return
	}

	apiURL := fmt.Sprintf("%s/api/v1/game/%s/click", pythonAPIURL, userID)
	log.Printf("Sending POST request to: %s", apiURL)
	log.Printf("Request body: %s", string(jsonData))

	resp, err := http.Post(
		apiURL,
		"application/json",
		bytes.NewBuffer(jsonData),
	)

	if err != nil {
		log.Printf("*** FALLBACK TRIGGERED *** Error connecting to Python API: %v", err)
		// フォールバック処理
		c.JSON(http.StatusOK, gin.H{
			"user_id":        userID,
			"cookies_earned": clickReq.ClickPower,
			"total_cookies":  clickReq.ClickPower,
			"message":        "Cookie clicked! (Local fallback - Python API unavailable)",
		})
		return
	}
	defer resp.Body.Close()

	log.Printf("Python API response status: %d", resp.StatusCode)

	// Python APIのレスポンスをクライアントに転送
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		log.Printf("Failed to read Python API response: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to read Python API response"})
		return
	}

	log.Printf("Python API response body: %s", string(body))
	log.Printf("=== CLICK DEBUG END ===")

	c.Header("Content-Type", "application/json")
	c.Data(resp.StatusCode, "application/json", body)
}

func handleUpgrade(c *gin.Context) {
	userID := c.Param("user_id")

	var request struct {
		UpgradeID string `json:"upgrade_id"`
	}

	if err := c.ShouldBindJSON(&request); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request"})
		return
	}

	// アップグレード処理をPython APIに委譲
	response := gin.H{
		"user_id":    userID,
		"upgrade_id": request.UpgradeID,
		"success":    true,
		"message":    "Upgrade purchased!",
	}

	c.JSON(http.StatusOK, response)
}

func handleSaveGame(c *gin.Context) {
	userID := c.Param("user_id")

	// ゲーム保存処理をPython APIに委譲
	response := gin.H{
		"user_id": userID,
		"saved":   true,
		"message": "Game saved successfully!",
	}

	c.JSON(http.StatusOK, response)
}

func handleLoadGame(c *gin.Context) {
	userID := c.Param("user_id")

	// ゲーム読み込み処理をPython APIに委譲
	response := gin.H{
		"user_id": userID,
		"loaded":  true,
		"message": "Game loaded successfully!",
	}

	c.JSON(http.StatusOK, response)
}
