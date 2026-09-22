package com.cofc.timeprotocol;

import com.google.gson.Gson;
import com.google.gson.JsonObject;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

public class TimeProtocolClient {
    private final String baseUrl;
    private final HttpClient httpClient;
    private final Gson gson;

    public TimeProtocolClient(String baseUrl) {
        this.baseUrl = baseUrl.replaceAll("/$", "");
        this.httpClient = HttpClient.newHttpClient();
        this.gson = new Gson();
    }

    public JsonObject getStatus() throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(baseUrl + "/v1/status"))
                .GET()
                .build();

        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        return gson.fromJson(response.body(), JsonObject.class);
    }

    public JsonObject proposeTransaction(String address, double balance, int nonce, double staked) throws Exception {
        JsonObject jsonBody = new JsonObject();
        jsonBody.addProperty("address", address);
        jsonBody.addProperty("balance", balance);
        jsonBody.addProperty("nonce", nonce);
        jsonBody.addProperty("staked", staked);

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(baseUrl + "/v1/transaction/propose"))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(gson.toJson(jsonBody)))
                .build();

        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        return gson.fromJson(response.body(), JsonObject.class);
    }
}
