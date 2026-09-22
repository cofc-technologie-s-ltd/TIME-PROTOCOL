/**
 * Official TypeScript SDK for TIME Protocol Core
 * By COFC Technologies LTD
 */
export class TimeProtocolClient {
    private baseUrl: string;

    constructor(baseUrl: string = "http://localhost:8000") {
        this.baseUrl = baseUrl.replace(/\/$/, "");
    }

    async getStatus(): Promise<any> {
        const response = await fetch(`${this.baseUrl}/v1/status`);
        return response.json();
    }

    async getAccount(address: string): Promise<any> {
        const response = await fetch(`${this.baseUrl}/v1/account/${address}`);
        return response.json();
    }

    async proposeTransaction(address: string, balance: number, nonce: number, staked: number = 0): Promise<any> {
        const response = await fetch(`${this.baseUrl}/v1/transaction/propose`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ address, balance, nonce, staked })
        });
        return response.json();
    }
}
