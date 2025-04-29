using System.Net.Http.Json;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Newtonsoft.Json;
using PriceFeed.Core.Interfaces;
using PriceFeed.Core.Models;
using PriceFeed.Core.Options;

namespace PriceFeed.Infrastructure.DataSources;

/// <summary>
/// Data source adapter for fetching price data from Coinbase
/// </summary>
public class CoinbaseDataSourceAdapter : IDataSourceAdapter
{
    private readonly HttpClient _httpClient;
    private readonly ILogger<CoinbaseDataSourceAdapter> _logger;
    private readonly CoinbaseOptions _options;
    private readonly SymbolMappingOptions _symbolMappings;

    /// <summary>
    /// Gets the name of the data source
    /// </summary>
    public string SourceName => "Coinbase";

    /// <summary>
    /// Checks if the data source is enabled (has API key configured)
    /// </summary>
    /// <returns>True if the data source is enabled, false otherwise</returns>
    public bool IsEnabled()
    {
        // Coinbase can work with public API for price data, but we'll check for API key
        // to determine if it's explicitly enabled
        bool hasApiKey = !string.IsNullOrEmpty(_options.ApiKey) && !string.IsNullOrEmpty(_options.ApiSecret);

        if (!hasApiKey)
        {
            _logger.LogWarning("Coinbase API key or secret is not configured. Coinbase data source is disabled.");
        }

        return hasApiKey;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="CoinbaseDataSourceAdapter"/> class
    /// </summary>
    /// <param name="httpClientFactory">The HTTP client factory</param>
    /// <param name="logger">The logger</param>
    /// <param name="options">The Coinbase options</param>
    public CoinbaseDataSourceAdapter(
        IHttpClientFactory httpClientFactory,
        ILogger<CoinbaseDataSourceAdapter> logger,
        IOptions<CoinbaseOptions> options,
        IOptions<PriceFeedOptions> priceFeedOptions)
    {
        _httpClient = httpClientFactory.CreateClient("Coinbase");
        _logger = logger;
        _options = options.Value;
        _symbolMappings = priceFeedOptions.Value.SymbolMappings;

        _httpClient.BaseAddress = new Uri(_options.BaseUrl);
        _httpClient.Timeout = TimeSpan.FromSeconds(_options.TimeoutSeconds);

        // Add API key header if available
        if (!string.IsNullOrEmpty(_options.ApiKey) && !string.IsNullOrEmpty(_options.ApiSecret))
        {
            // Authentication is handled through the HTTP client factory configuration
            // Using public API endpoints when authentication is not available
        }
    }

    /// <summary>
    /// Gets the list of symbols supported by Coinbase
    /// </summary>
    /// <returns>A list of supported symbols</returns>
    public Task<IEnumerable<string>> GetSupportedSymbolsAsync()
    {
        // Return all symbols that are supported by Coinbase
        return Task.FromResult<IEnumerable<string>>(_symbolMappings.GetSymbolsForDataSource(SourceName));
    }

    /// <summary>
    /// Fetches the current price data for a specific symbol
    /// </summary>
    /// <param name="symbol">The standard symbol to fetch price data for</param>
    /// <returns>The price data for the specified symbol</returns>
    public async Task<PriceData> GetPriceDataAsync(string symbol)
    {
        try
        {
            // Check if this symbol is supported by Coinbase
            if (!_symbolMappings.IsSymbolSupportedBySource(symbol, SourceName))
            {
                _logger.LogWarning("Symbol {Symbol} is not supported by {Source}", symbol, SourceName);
                throw new NotSupportedException($"Symbol {symbol} is not supported by {SourceName}");
            }

            // Get the Coinbase-specific symbol format
            var coinbaseSymbol = _symbolMappings.GetSourceSymbol(symbol, SourceName);

            // Parse the Coinbase symbol format (expected format: "BTC-USD")
            string[] parts = coinbaseSymbol.Split('-');
            if (parts.Length != 2)
            {
                _logger.LogWarning("Invalid Coinbase symbol format: {Symbol}", coinbaseSymbol);
                throw new FormatException($"Invalid Coinbase symbol format: {coinbaseSymbol}");
            }

            var baseCurrency = parts[0];
            var quoteCurrency = parts[1];

            // Build the request URL
            var endpoint = $"{_options.SpotPriceEndpoint}/{baseCurrency}-{quoteCurrency}/spot";
            var response = await _httpClient.GetAsync(endpoint);
            response.EnsureSuccessStatusCode();

            var content = await response.Content.ReadAsStringAsync();
            var spotPriceResponse = JsonConvert.DeserializeObject<CoinbaseSpotPriceResponse>(content);

            if (spotPriceResponse?.Data == null)
            {
                _logger.LogWarning("Failed to get price data for symbol {Symbol} from Coinbase: Response is invalid", symbol);
                throw new Exception($"Failed to get price data for symbol {symbol} from Coinbase");
            }

            // Volume information is not directly available from the spot price endpoint
            // Volume data would require additional API calls to trading endpoints
            decimal? volume = null;

            return new PriceData
            {
                Symbol = symbol,
                Price = decimal.Parse(spotPriceResponse.Data.Amount),
                Source = SourceName,
                Timestamp = DateTime.UtcNow,
                Volume = volume,
                Metadata = new Dictionary<string, string>
                {
                    { "BaseCurrency", baseCurrency },
                    { "QuoteCurrency", quoteCurrency },
                    { "SourceSymbol", coinbaseSymbol } // Store the source-specific symbol in metadata
                }
            };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting price data for symbol {Symbol} from Coinbase", symbol);
            throw;
        }
    }

    /// <summary>
    /// Fetches the current price data for multiple symbols
    /// </summary>
    /// <param name="symbols">The standard symbols to fetch price data for</param>
    /// <returns>A collection of price data for the specified symbols</returns>
    public async Task<IEnumerable<PriceData>> GetPriceDataBatchAsync(IEnumerable<string> symbols)
    {
        // Filter out symbols that are not supported by Coinbase
        var supportedSymbols = symbols
            .Where(s => _symbolMappings.IsSymbolSupportedBySource(s, SourceName))
            .ToList();

        if (!supportedSymbols.Any())
        {
            _logger.LogWarning("No supported symbols found for {Source}", SourceName);
            return Enumerable.Empty<PriceData>();
        }

        var results = new List<PriceData>();

        foreach (var symbol in supportedSymbols)
        {
            try
            {
                var result = await GetPriceDataAsync(symbol);
                results.Add(result);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error getting price data for symbol {Symbol} from Coinbase", symbol);
                // Continue with other symbols
            }
        }

        return results;
    }
}

/// <summary>
/// Response from Coinbase spot price API
/// </summary>
internal class CoinbaseSpotPriceResponse
{
    [JsonProperty("data")]
    public CoinbaseSpotPriceData Data { get; set; } = new();
}

/// <summary>
/// Spot price data from Coinbase
/// </summary>
internal class CoinbaseSpotPriceData
{
    [JsonProperty("base")]
    public string Base { get; set; } = string.Empty;

    [JsonProperty("currency")]
    public string Currency { get; set; } = string.Empty;

    [JsonProperty("amount")]
    public string Amount { get; set; } = string.Empty;
}
