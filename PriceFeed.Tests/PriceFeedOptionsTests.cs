using System;
using Microsoft.Extensions.Options;
using PriceFeed.Core.Options;
using Xunit;

namespace PriceFeed.Tests
{
    public class PriceFeedOptionsTests
    {
        [Fact]
        public void Constructor_WithValidSymbols_ShouldParseCorrectly()
        {
            // Arrange
            Environment.SetEnvironmentVariable("SYMBOLS", "BTCUSDT,ETHBTC,NEOBTC");

            // Act
            var options = new PriceFeedOptions();

            // Assert
            Assert.Equal(3, options.Symbols.Count);
            Assert.Contains("BTCUSDT", options.Symbols);
            Assert.Contains("ETHBTC", options.Symbols);
            Assert.Contains("NEOBTC", options.Symbols);

            // Cleanup
            Environment.SetEnvironmentVariable("SYMBOLS", null);
        }

        [Fact]
        public void Constructor_WithInvalidSymbols_ShouldFilterThem()
        {
            // Arrange
            Environment.SetEnvironmentVariable("SYMBOLS", "BTCUSDT,ETH-BTC,123,AB");

            // Act
            var options = new PriceFeedOptions();

            // Assert
            Assert.Contains("BTCUSDT", options.Symbols);
            Assert.Contains("123", options.Symbols);
            Assert.Contains("ETHBTC", options.Symbols);

            // Cleanup
            Environment.SetEnvironmentVariable("SYMBOLS", null);
        }

        [Fact]
        public void Constructor_WithNoSymbols_ShouldUseDefaults()
        {
            // Arrange
            Environment.SetEnvironmentVariable("SYMBOLS", null);

            // Act
            var options = new PriceFeedOptions();

            // Assert
            Assert.Equal(3, options.Symbols.Count);
            Assert.Contains("NEOBTC", options.Symbols);
            Assert.Contains("NEOUSDT", options.Symbols);
            Assert.Contains("BTCUSDT", options.Symbols);
        }

        [Fact]
        public void Constructor_WithDuplicateSymbols_ShouldRemoveDuplicates()
        {
            // Arrange
            Environment.SetEnvironmentVariable("SYMBOLS", "BTCUSDT,btcusdt,ETHBTC");

            // Act
            var options = new PriceFeedOptions();

            // Assert
            Assert.Equal(2, options.Symbols.Count);
            Assert.Contains("BTCUSDT", options.Symbols);
            Assert.Contains("ETHBTC", options.Symbols);

            // Cleanup
            Environment.SetEnvironmentVariable("SYMBOLS", null);
        }
    }
}
