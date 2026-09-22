package timeprotocol

import (
"bytes"
"encoding/json"
"fmt"
"net/http"
"strings"
)

type Client struct {
BaseURL    string
HTTPClient *http.Client
}

type TransactionRequest struct {
Address string  `json:"address"`
Balance float64 `json:"balance"`
Nonce   int     `json:"nonce"`
Staked  float64 `json:"staked"`
}

func NewClient(baseURL string) *Client {
return &Client{
   strings.TrimRight(baseURL, "/"),
t: &http.Client{},
}
}

func (c *Client) GetStatus() (map[string]interface{}, error) {
resp, err := c.HTTPClient.Get(c.BaseURL + "/v1/status")
if err != nil {
 nil, err
}
defer resp.Body.Close()

var result map[string]interface{}
json.NewDecoder(resp.Body).Decode(&result)
return result, nil
}

func (c *Client) ProposeTransaction(req TransactionRequest) (map[string]interface{}, error) {
body, err := json.Marshal(req)
if err != nil {
 nil, err
}

resp, err := c.HTTPClient.Post(c.BaseURL+"/v1/transaction/propose", "application/json", bytes.NewBuffer(body))
if err != nil {
 nil, err
}
defer resp.Body.Close()

var result map[string]interface{}
json.NewDecoder(resp.Body).Decode(&result)
return result, nil
}
