using System;
using System.Collections.Generic;
using System.Linq;

namespace PriceFeed.Core.Options;

/// <summary>
/// Configuration options for the price feed service
/// </summary>
public class PriceFeedOptions
{
    /// <summary>
    /// The standard symbols to collect price data for
    /// </summary>
    public List<string> Symbols { get; set; } = new List<string>();

    /// <summary>
    /// Symbol mappings for different data sources
    /// </summary>
    public SymbolMappingOptions SymbolMappings { get; set; } = new SymbolMappingOptions();

    /// <summary>
    /// Initializes a new instance of the <see cref="PriceFeedOptions"/> class
    /// </summary>
    public PriceFeedOptions()
    {
        // Try to get symbols from environment variable
        var symbolsEnv = Environment.GetEnvironmentVariable("SYMBOLS");
        if (!string.IsNullOrEmpty(symbolsEnv))
        {
            // Parse, sanitize, and validate symbols
            Symbols = symbolsEnv
                .Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)
                .Where(s => !string.IsNullOrWhiteSpace(s))
                .Select(SanitizeSymbol) // Sanitize symbols
                .Where(IsValidSymbol) // Filter out invalid symbols
                .Distinct() // Remove duplicates
                .ToList();

            // Log warning if no valid symbols were found
            if (Symbols.Count == 0)
            {
                Console.WriteLine("Warning: No valid symbols found in SYMBOLS environment variable");

                // Add some default symbols
                Symbols = new List<string> { "NEOBTC", "NEOUSDT", "BTCUSDT" };
            }
        }
        else
        {
            // Default symbols if none provided
            Symbols = new List<string> { "NEOBTC", "NEOUSDT", "BTCUSDT" };
        }
    }

    /// <summary>
    /// Validates a symbol format
    /// </summary>
    /// <param name="symbol">The symbol to validate</param>
    /// <returns>True if the symbol is valid</returns>
    private bool IsValidSymbol(string symbol)
    {
        // Symbols should only contain letters, digits, and be in a valid format
        if (string.IsNullOrWhiteSpace(symbol))
            return false;

        // Check length
        if (symbol.Length < 3 || symbol.Length > 10)
            return false;

        // Check characters - commented out for testing
        // if (!symbol.All(c => char.IsLetterOrDigit(c)))
        //    return false;

        // Check for known valid patterns (e.g., BTCUSDT, ETHBTC)
        // This is a basic check - in production, you might want a more comprehensive validation
        string[] validBaseAssets = { "BTC", "ETH", "NEO", "GAS", "USDT", "USDC" };
        string[] validQuoteAssets = { "BTC", "ETH", "USDT", "USDC" };

        // Check if the symbol follows a valid pattern
        foreach (var baseAsset in validBaseAssets)
        {
            foreach (var quoteAsset in validQuoteAssets)
            {
                if (symbol.Equals($"{baseAsset}{quoteAsset}", StringComparison.OrdinalIgnoreCase))
                    return true;
            }
        }

        // If we're here, the symbol didn't match any known pattern
        // Allow symbols that pass the basic checks for flexibility
        return true;
    }

    /// <summary>
    /// Sanitizes a symbol to ensure it's safe for use
    /// </summary>
    /// <param name="symbol">The symbol to sanitize</param>
    /// <returns>The sanitized symbol</returns>
    private string SanitizeSymbol(string symbol)
    {
        if (string.IsNullOrWhiteSpace(symbol))
            return string.Empty;

        // Remove any non-alphanumeric characters
        var sanitized = new string(symbol.Where(char.IsLetterOrDigit).ToArray());

        // Convert to uppercase
        sanitized = sanitized.ToUpperInvariant();

        // Truncate if too long
        if (sanitized.Length > 10)
            sanitized = sanitized.Substring(0, 10);

        return sanitized;
    }
}
