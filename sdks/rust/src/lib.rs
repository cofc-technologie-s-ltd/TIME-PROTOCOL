use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::error::Error;

#[derive(Serialize, Deserialize, Debug)]
pub struct TransactionRequest {
    pub address: String,
    pub balance: f64,
    pub nonce: i32,
    pub staked: f64,
}

pub struct TimeProtocolClient {
    base_url: String,
    client: Client,
}

impl TimeProtocolClient {
    pub fn new(base_url: &str) -> Self {
        Self {
            base_url: base_url.trim_end_matches('/').to_string(),
            client: Client::new(),
        }
    }

    pub async fn get_status(&self) -> Result<serde_json::Value, Box<dyn Error>> {
        let url = format!("{}/v1/status", self.base_url);
        let resp = self.client.get(&url).send().await?.json::<serde_json::Value>().await?;
        Ok(resp)
    }

    pub async fn propose_transaction(&self, req: &TransactionRequest) -> Result<serde_json::Value, Box<dyn Error>> {
        let url = format!("{}/v1/transaction/propose", self.base_url);
        let resp = self.client.post(&url)
            .json(req)
            .send()
            .await?
            .json::<serde_json::Value>().await?;
        Ok(resp)
    }
}
