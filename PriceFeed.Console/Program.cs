using System.Diagnostics;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Newtonsoft.Json;
using PriceFeed.Core.Interfaces;
using PriceFeed.Core.Models;
using PriceFeed.Core.Options;
using PriceFeed.Console;
using PriceFeed.Infrastructure.DataSources;
using PriceFeed.Infrastructure.Services;
using Serilog;
using Serilog.Events;

// Configure Serilog
Log.Logger = new LoggerConfiguration()
    .MinimumLevel.Information()
    .MinimumLevel.Override("Microsoft", LogEventLevel.Warning)
    .Enrich.FromLogContext()
    .Enrich.WithProperty("Application", "PriceFeed")
    .WriteTo.Console(outputTemplate: "[{Timestamp:HH:mm:ss} {Level:u3}] {Message:lj}{NewLine}{Exception}")
    .CreateLogger();

try
{
    // Check command line arguments
    var commandLineArgs = Environment.GetCommandLineArgs();

    // Account generation mode
    if (commandLineArgs.Contains("--generate-account"))
    {
        // Check if secure output is requested
        string secureOutputPath = null;
        for (int i = 0; i < commandLineArgs.Length - 1; i++)
        {
            if (commandLineArgs[i] == "--secure-output")
            {
                secureOutputPath = commandLineArgs[i + 1];
                break;
            }
        }

        GenerateNeoAccount(secureOutputPath);
        return 0;
    }

    // Create account attestation mode
    if (commandLineArgs.Contains("--create-account-attestation"))
    {
        // Get the account address from command line
        string accountAddress = null;
        for (int i = 0; i < commandLineArgs.Length - 1; i++)
        {
            if (commandLineArgs[i] == "--account-address")
            {
                accountAddress = commandLineArgs[i + 1];
                break;
            }
        }

        if (string.IsNullOrEmpty(accountAddress))
        {
            Log.Error("Account address is required for attestation");
            return 1;
        }

        await CreateAccountAttestationAsync(accountAddress);
        return 0;
    }

    // Verify account attestation mode
    if (commandLineArgs.Contains("--verify-account-attestation"))
    {
        bool isValid = await VerifyAccountAttestationAsync();
        return isValid ? 0 : 1;
    }

    // Test symbol mappings mode
    if (commandLineArgs.Contains("--test-symbol-mappings"))
    {
        SymbolMappingTest.RunTest();
        return 0;
    }

    // Check if we should skip health checks
    bool skipHealthChecks = commandLineArgs.Contains("--skip-health-checks");

    Log.Information("Starting PriceFeed job");

    // Check for sensitive environment variables
    CheckSensitiveEnvironmentVariables();

    // Create and configure the host
    using var host = Host.CreateDefaultBuilder(commandLineArgs)
        .UseSerilog()
        .ConfigureAppConfiguration((hostContext, config) =>
        {
            config.AddJsonFile("appsettings.json", optional: true, reloadOnChange: true);
            config.AddJsonFile($"appsettings.{hostContext.HostingEnvironment.EnvironmentName}.json", optional: true, reloadOnChange: true);
            config.AddEnvironmentVariables();
            config.AddCommandLine(commandLineArgs);
        })
        .ConfigureServices((hostContext, services) =>
        {
            // Configure options
            services.Configure<PriceFeedOptions>(hostContext.Configuration.GetSection("PriceFeed"));
            services.Configure<BinanceOptions>(hostContext.Configuration.GetSection("Binance"));
            services.Configure<CoinMarketCapOptions>(hostContext.Configuration.GetSection("CoinMarketCap"));
            services.Configure<CoinbaseOptions>(hostContext.Configuration.GetSection("Coinbase"));
            services.Configure<OKExOptions>(hostContext.Configuration.GetSection("OKEx"));
            services.Configure<BatchProcessingOptions>(hostContext.Configuration.GetSection("BatchProcessing"));

            // Register HTTP clients
            services.AddHttpClient();

            // Configure Binance HTTP client
            services.AddHttpClient("Binance", (serviceProvider, client) =>
            {
                var options = serviceProvider.GetRequiredService<IOptions<BinanceOptions>>().Value;
                client.BaseAddress = new Uri(options.BaseUrl);
                client.DefaultRequestHeaders.Add("Accept", "application/json");
                client.Timeout = TimeSpan.FromSeconds(options.TimeoutSeconds);
            });

            // Configure CoinMarketCap HTTP client
            services.AddHttpClient("CoinMarketCap", (serviceProvider, client) =>
            {
                var options = serviceProvider.GetRequiredService<IOptions<CoinMarketCapOptions>>().Value;
                client.BaseAddress = new Uri(options.BaseUrl);
                client.DefaultRequestHeaders.Add("Accept", "application/json");
                client.Timeout = TimeSpan.FromSeconds(options.TimeoutSeconds);
                if (!string.IsNullOrEmpty(options.ApiKey))
                {
                    client.DefaultRequestHeaders.Add("X-CMC_PRO_API_KEY", options.ApiKey);
                }
            });

            // Configure Coinbase HTTP client
            services.AddHttpClient("Coinbase", (serviceProvider, client) =>
            {
                var options = serviceProvider.GetRequiredService<IOptions<CoinbaseOptions>>().Value;
                client.BaseAddress = new Uri(options.BaseUrl);
                client.DefaultRequestHeaders.Add("Accept", "application/json");
                client.Timeout = TimeSpan.FromSeconds(options.TimeoutSeconds);
            });

            // Configure OKEx HTTP client
            services.AddHttpClient("OKEx", (serviceProvider, client) =>
            {
                var options = serviceProvider.GetRequiredService<IOptions<OKExOptions>>().Value;
                client.BaseAddress = new Uri(options.BaseUrl);
                client.DefaultRequestHeaders.Add("Accept", "application/json");
                client.Timeout = TimeSpan.FromSeconds(options.TimeoutSeconds);
                if (!string.IsNullOrEmpty(options.ApiKey))
                {
                    client.DefaultRequestHeaders.Add("OK-ACCESS-KEY", options.ApiKey);
                }
            });

            // Configure Neo HTTP client
            services.AddHttpClient("Neo", client =>
            {
                client.DefaultRequestHeaders.Add("Accept", "application/json");
            });

            // Register data source adapters
            services.AddTransient<IDataSourceAdapter, BinanceDataSourceAdapter>();
            services.AddTransient<IDataSourceAdapter, CoinMarketCapDataSourceAdapter>();
            services.AddTransient<IDataSourceAdapter, CoinbaseDataSourceAdapter>();
            services.AddTransient<IDataSourceAdapter, OKExDataSourceAdapter>();

            // Register symbol mapping service
            services.AddSingleton<SymbolMappingOptions>(sp =>
                sp.GetRequiredService<IOptions<PriceFeedOptions>>().Value.SymbolMappings);

            // Register services
            services.AddTransient<IPriceAggregationService, PriceAggregationService>();
            services.AddTransient<IBatchProcessingService, BatchProcessingService>();
            services.AddSingleton<RateLimiter>();
            services.AddSingleton<IAttestationService, AttestationService>();

            // Configure rate limiter
            var serviceProvider = services.BuildServiceProvider();
            var rateLimiter = serviceProvider.GetRequiredService<RateLimiter>();
            rateLimiter.Configure("Binance", 10); // 10 requests per second
            rateLimiter.Configure("CoinMarketCap", 5); // 5 requests per second
            rateLimiter.Configure("Coinbase", 5); // 5 requests per second
            rateLimiter.Configure("OKEx", 5); // 5 requests per second

            // Register the main job
            services.AddTransient<PriceFeedJob>();
        })
        .Build();

    // Run the job
    var job = host.Services.GetRequiredService<PriceFeedJob>();
    await job.RunAsync(skipHealthChecks);

    Log.Information("PriceFeed job completed successfully");
    return 0;
}
catch (Exception ex)
{
    Log.Fatal(ex, "PriceFeed job terminated unexpectedly");
    return 1;
}
finally
{
    Log.CloseAndFlush();
}

/// <summary>
/// Checks for sensitive environment variables and warns if they're not set
/// </summary>
static void CheckSensitiveEnvironmentVariables()
{
    // List of required environment variables
    var requiredVariables = new[]
    {
        "NEO_RPC_ENDPOINT",
        "NEO_CONTRACT_HASH",
        "NEO_ACCOUNT_ADDRESS",
        "NEO_ACCOUNT_PRIVATE_KEY"
    };

    // List of optional but recommended environment variables
    var recommendedVariables = new[]
    {
        "BINANCE_API_KEY",
        "BINANCE_API_SECRET",
        "COINMARKETCAP_API_KEY",
        "COINBASE_API_KEY",
        "COINBASE_API_SECRET",
        "OKEX_API_KEY",
        "OKEX_API_SECRET",
        "OKEX_PASSPHRASE"
    };

    // Check required variables
    var missingRequired = requiredVariables
        .Where(v => string.IsNullOrEmpty(Environment.GetEnvironmentVariable(v)))
        .ToList();

    if (missingRequired.Any())
    {
        Log.Error("Missing required environment variables: {Variables}", string.Join(", ", missingRequired));
        throw new InvalidOperationException($"Missing required environment variables: {string.Join(", ", missingRequired)}");
    }

    // Check recommended variables
    var missingRecommended = recommendedVariables
        .Where(v => string.IsNullOrEmpty(Environment.GetEnvironmentVariable(v)))
        .ToList();

    if (missingRecommended.Any())
    {
        Log.Warning("Missing recommended environment variables: {Variables}", string.Join(", ", missingRecommended));
    }

    // Warn about sensitive data
    Log.Information("Sensitive environment variables are set. Make sure they are securely stored in GitHub Secrets.");
}

/// <summary>
/// Generates a new Neo TEE account and outputs the address and WIF
/// </summary>
/// <param name="secureOutputPath">Optional path to write the account information to a file instead of stdout</param>
static void GenerateNeoAccount(string secureOutputPath = null)
{
    try
    {
        Log.Information("Generating new Neo TEE account...");

        // Generate a simulated Neo account for demonstration purposes
        // Note: This is a simplified implementation for the TEE environment

        // Generate a random private key
        byte[] privateKey = new byte[32];
        using (var rng = RandomNumberGenerator.Create())
        {
            rng.GetBytes(privateKey);
        }

        // Convert to hex string (this is a simplified example)
        string privateKeyHex = BitConverter.ToString(privateKey).Replace("-", "").ToLowerInvariant();

        // Derive a WIF (simplified example)
        string wif = $"L{Convert.ToBase64String(privateKey).Substring(0, 22)}";

        // Derive an address (simplified example)
        using var sha256 = SHA256.Create();
        var addressBytes = sha256.ComputeHash(privateKey);
        string address = $"N{Convert.ToBase64String(addressBytes).Substring(0, 22)}";

        // Output the account information
        if (!string.IsNullOrEmpty(secureOutputPath))
        {
            // Write to secure file instead of stdout
            var accountInfo = $"Address: {address}\nWIF: {wif}";

            // Ensure directory exists
            var directory = Path.GetDirectoryName(secureOutputPath);
            if (!string.IsNullOrEmpty(directory) && !Directory.Exists(directory))
            {
                Directory.CreateDirectory(directory);
            }

            // Write to file with restricted permissions
            File.WriteAllText(secureOutputPath, accountInfo);

            // Set restrictive permissions on the file (Unix-like systems)
            if (OperatingSystem.IsLinux() || OperatingSystem.IsMacOS())
            {
                try
                {
                    // Use chmod to set permissions to owner-only (600)
                    var process = new Process
                    {
                        StartInfo = new ProcessStartInfo
                        {
                            FileName = "chmod",
                            Arguments = $"600 {secureOutputPath}",
                            RedirectStandardOutput = true,
                            UseShellExecute = false,
                            CreateNoWindow = true,
                        }
                    };
                    process.Start();
                    process.WaitForExit();
                }
                catch (Exception ex)
                {
                    Log.Warning(ex, "Failed to set restrictive permissions on the secure output file");
                }
            }

            Log.Information("Neo TEE account information written to secure file: {FilePath}", secureOutputPath);
        }
        else
        {
            // Output to stdout (this will be captured by the GitHub Actions workflow)
            // Note: This is less secure as it will appear in logs
            Console.WriteLine($"Address: {address}");
            Console.WriteLine($"WIF: {wif}");
        }

        Log.Information("Neo TEE account generated successfully");
    }
    catch (Exception ex)
    {
        Log.Error(ex, "Error generating Neo account");
        throw;
    }
}

/// <summary>
/// Creates an attestation for the TEE account
/// </summary>
/// <param name="accountAddress">The TEE account address</param>
static async Task CreateAccountAttestationAsync(string accountAddress)
{
    try
    {
        Log.Information("Creating attestation for TEE account {AccountAddress}", accountAddress);

        // Build a host to get the AttestationService
        var host = Host.CreateDefaultBuilder()
            .ConfigureServices(services =>
            {
                // Register the AttestationService
                services.AddLogging(builder => builder.AddSerilog());
                services.AddSingleton<AttestationService>();
            })
            .Build();

        // Get the AttestationService
        var attestationService = host.Services.GetRequiredService<AttestationService>();

        // Get GitHub Actions environment variables
        var runId = Environment.GetEnvironmentVariable("GITHUB_RUN_ID") ?? "unknown";
        var runNumber = Environment.GetEnvironmentVariable("GITHUB_RUN_NUMBER") ?? "unknown";
        var repository = Environment.GetEnvironmentVariable("GITHUB_REPOSITORY") ?? "unknown";
        var workflow = Environment.GetEnvironmentVariable("GITHUB_WORKFLOW") ?? "unknown";

        // Split repository into owner and name
        var repoSplit = repository.Split('/');
        var repoOwner = repoSplit.Length > 0 ? repoSplit[0] : "unknown";
        var repoName = repoSplit.Length > 1 ? repoSplit[1] : "unknown";

        // Create attestation
        var attestation = await attestationService.CreateAccountAttestationAsync(
            accountAddress,
            runId,
            runNumber,
            repoOwner,
            repoName,
            workflow);

        Log.Information("Account attestation created successfully");
    }
    catch (Exception ex)
    {
        Log.Error(ex, "Error creating account attestation");
        throw;
    }
}

/// <summary>
/// Verifies the TEE account attestation and checks for Master account
/// </summary>
/// <returns>True if the attestation is valid and accounts are properly configured</returns>
static async Task<bool> VerifyAccountAttestationAsync()
{
    try
    {
        Log.Information("Verifying TEE account attestation and checking for Master account");

        // Build a host to get the AttestationService
        var host = Host.CreateDefaultBuilder()
            .ConfigureServices(services =>
            {
                // Register the AttestationService
                services.AddLogging(builder => builder.AddSerilog());
                services.AddSingleton<AttestationService>();
            })
            .Build();

        // Get the AttestationService
        var attestationService = host.Services.GetRequiredService<AttestationService>();

        // Read the attestation file
        var attestationPath = Path.Combine("attestations", "account_attestation.json");
        if (!File.Exists(attestationPath))
        {
            Log.Error("Account attestation file not found at {Path}", attestationPath);
            return false;
        }

        var attestationJson = await File.ReadAllTextAsync(attestationPath);
        var attestation = JsonConvert.DeserializeObject<AccountAttestationData>(attestationJson);

        if (attestation == null)
        {
            Log.Error("Failed to parse account attestation");
            return false;
        }

        // Verify the attestation
        bool isValid = attestationService.VerifyAccountAttestation(attestation);

        if (isValid)
        {
            Log.Information("TEE account attestation is valid for address {AccountAddress}", attestation.AccountAddress);

            // Verify that the account address matches the TEE account in GitHub Secrets
            var teeAccountAddress = Environment.GetEnvironmentVariable("NEO_TEE_ACCOUNT_ADDRESS");

            // For backward compatibility, also check the old environment variable
            if (string.IsNullOrEmpty(teeAccountAddress))
            {
                teeAccountAddress = Environment.GetEnvironmentVariable("NEO_ACCOUNT_ADDRESS");
            }

            if (string.IsNullOrEmpty(teeAccountAddress))
            {
                Log.Warning("Neither NEO_TEE_ACCOUNT_ADDRESS nor NEO_ACCOUNT_ADDRESS environment variables are set");
            }
            else if (teeAccountAddress != attestation.AccountAddress)
            {
                Log.Error("Account address in attestation ({AttestationAddress}) does not match TEE account address ({EnvAddress})",
                    attestation.AccountAddress, teeAccountAddress);
                return false;
            }

            // Also verify that the Master account is set
            var masterAccountAddress = Environment.GetEnvironmentVariable("NEO_MASTER_ACCOUNT_ADDRESS");
            if (string.IsNullOrEmpty(masterAccountAddress))
            {
                Log.Warning("NEO_MASTER_ACCOUNT_ADDRESS environment variable is not set. " +
                           "This is required for the dual-signature transaction system.");
            }

            return true;
        }
        else
        {
            Log.Error("Account attestation is invalid");
            return false;
        }
    }
    catch (Exception ex)
    {
        Log.Error(ex, "Error verifying account attestation");
        return false;
    }
}

/// <summary>
/// Main job class that runs the price feed process
/// </summary>
public class PriceFeedJob
{
    private readonly ILogger<PriceFeedJob> _logger;
    private readonly PriceFeedOptions _options;
    private readonly SymbolMappingOptions _symbolMappings;
    private readonly IEnumerable<IDataSourceAdapter> _dataSourceAdapters;
    private readonly IPriceAggregationService _aggregationService;
    private readonly IBatchProcessingService _batchProcessingService;
    private readonly AttestationService _attestationService;

    /// <summary>
    /// Initializes a new instance of the <see cref="PriceFeedJob"/> class
    /// </summary>
    public PriceFeedJob(
        ILogger<PriceFeedJob> logger,
        IOptions<PriceFeedOptions> options,
        SymbolMappingOptions symbolMappings,
        IEnumerable<IDataSourceAdapter> dataSourceAdapters,
        IPriceAggregationService aggregationService,
        IBatchProcessingService batchProcessingService,
        AttestationService attestationService)
    {
        _logger = logger;
        _options = options.Value;
        _symbolMappings = symbolMappings;
        _dataSourceAdapters = dataSourceAdapters;
        _aggregationService = aggregationService;
        _batchProcessingService = batchProcessingService;
        _attestationService = attestationService;
    }

    /// <summary>
    /// Runs the price feed job
    /// </summary>
    /// <param name="skipHealthChecks">Parameter kept for backward compatibility but no longer used</param>
    public async Task RunAsync(bool skipHealthChecks = false)
    {
        _logger.LogInformation("Starting price feed job with {Count} symbols: {Symbols}",
            _options.Symbols.Count, string.Join(", ", _options.Symbols));

        // Log symbol mappings
        _logger.LogInformation("Symbol mappings configured for {Count} symbols", _symbolMappings.Mappings.Count);

        try
        {
            // 1. Collect price data from all enabled sources
            var priceDataBySymbol = new Dictionary<string, List<PriceData>>();

            // Filter out disabled data sources
            var enabledAdapters = _dataSourceAdapters.Where(adapter => adapter.IsEnabled()).ToList();

            if (!enabledAdapters.Any())
            {
                _logger.LogWarning("No enabled data sources found. Please configure at least one data source API key.");
                throw new InvalidOperationException("No enabled data sources found. Please configure at least one data source API key.");
            }

            _logger.LogInformation("Using {Count} enabled data sources: {Sources}",
                enabledAdapters.Count,
                string.Join(", ", enabledAdapters.Select(a => a.SourceName)));

            foreach (var adapter in enabledAdapters)
            {
                try
                {
                    _logger.LogInformation("Collecting price data from {Source}", adapter.SourceName);
                    var priceData = await adapter.GetPriceDataBatchAsync(_options.Symbols);

                    foreach (var data in priceData)
                    {
                        if (!priceDataBySymbol.ContainsKey(data.Symbol))
                        {
                            priceDataBySymbol[data.Symbol] = new List<PriceData>();
                        }

                        priceDataBySymbol[data.Symbol].Add(data);
                    }

                    _logger.LogInformation("Collected {Count} price data points from {Source}",
                        priceData.Count(), adapter.SourceName);
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Error collecting price data from {Source}", adapter.SourceName);
                }
            }

            if (!priceDataBySymbol.Any())
            {
                _logger.LogWarning("No price data collected from any source");
                // Instead of just returning, we'll throw a specific exception that can be caught and handled
                throw new InvalidOperationException("Failed to collect price data from any source. Check API keys and network connectivity.");
            }

            // 2. Aggregate price data
            _logger.LogInformation("Aggregating price data for {Count} symbols", priceDataBySymbol.Count);

            var aggregatedPrices = await _aggregationService.AggregateBatchAsync(
                priceDataBySymbol.ToDictionary(
                    kvp => kvp.Key,
                    kvp => kvp.Value as IEnumerable<PriceData>));

            if (!aggregatedPrices.Any())
            {
                _logger.LogWarning("No aggregated prices to send");
                throw new InvalidOperationException("Failed to aggregate price data. Check if the aggregation service is working correctly.");
            }

            // 3. Create and process batch
            _logger.LogInformation("Creating batch with {Count} aggregated prices", aggregatedPrices.Count());

            var batch = new PriceBatch
            {
                Prices = aggregatedPrices.ToList()
            };

            // 4. Send batch to smart contract with retry logic
            _logger.LogInformation("Sending batch {BatchId} to smart contract", batch.BatchId);

            const int maxRetries = 3;
            const int retryDelayMs = 5000; // 5 seconds
            bool success = false;

            for (int retry = 0; retry < maxRetries; retry++)
            {
                try
                {
                    success = await _batchProcessingService.ProcessBatchAsync(batch);

                    if (success)
                    {
                        _logger.LogInformation("Successfully processed batch {BatchId} with {Count} prices",
                            batch.BatchId, batch.Prices.Count);
                        break;
                    }
                    else
                    {
                        _logger.LogWarning("Failed to process batch {BatchId} (Attempt {Attempt}/{MaxAttempts})",
                            batch.BatchId, retry + 1, maxRetries);

                        if (retry < maxRetries - 1)
                        {
                            _logger.LogInformation("Retrying in {Delay}ms...", retryDelayMs);
                            await Task.Delay(retryDelayMs);
                        }
                    }
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Error processing batch {BatchId} (Attempt {Attempt}/{MaxAttempts})",
                        batch.BatchId, retry + 1, maxRetries);

                    if (retry < maxRetries - 1)
                    {
                        _logger.LogInformation("Retrying in {Delay}ms...", retryDelayMs);
                        await Task.Delay(retryDelayMs);
                    }
                }
            }

            if (!success)
            {
                _logger.LogError("Failed to process batch {BatchId} after {MaxAttempts} attempts",
                    batch.BatchId, maxRetries);
            }

            // 5. Log detailed price information
            foreach (var price in batch.Prices)
            {
                _logger.LogInformation("Price for {Symbol}: {Price} (Confidence: {Confidence}%)",
                    price.Symbol, price.Price, price.ConfidenceScore);
            }

            // 6. Clean up old attestations
            try
            {
                // Keep attestations for 7 days
                const int retentionDays = 7;

                _logger.LogInformation("Cleaning up attestations older than {RetentionDays} days", retentionDays);
                int removedCount = await _attestationService.CleanupOldAttestationsAsync(retentionDays);

                if (removedCount > 0)
                {
                    _logger.LogInformation("Removed {Count} old attestation files", removedCount);
                }
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Error cleaning up old attestations");
                // Continue processing - cleanup failure shouldn't stop the price feed
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error running price feed job");
            throw;
        }
    }
}
