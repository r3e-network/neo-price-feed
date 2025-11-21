using System;
using Xunit;

namespace PriceFeed.Tests.TestUtilities;

/// <summary>
/// Helper class for managing tests in CI environment
/// </summary>
public static class CITestHelper
{
    /// <summary>
    /// Checks if tests are running in CI environment
    /// </summary>
    public static bool IsRunningInCI =>
        Environment.GetEnvironmentVariable("CI") == "true" ||
        Environment.GetEnvironmentVariable("GITHUB_ACTIONS") == "true" ||
        Environment.GetEnvironmentVariable("TF_BUILD") == "True";

    /// <summary>
    /// Fact attribute that skips integration tests in CI
    /// </summary>
    public class IntegrationFactAttribute : FactAttribute
    {
        public IntegrationFactAttribute()
        {
            // Opt-in via RUN_INTEGRATION_TESTS=true; otherwise skip by default or in CI
            if (Environment.GetEnvironmentVariable("RUN_INTEGRATION_TESTS") != "true" || IsRunningInCI)
            {
                Skip = "Integration tests are skipped by default. Set RUN_INTEGRATION_TESTS=true to run.";
            }

            // Also set the timeout
            Timeout = 30000;
        }
    }

    /// <summary>
    /// Fact attribute that skips live API tests unless explicitly enabled.
    /// </summary>
    public class LiveApiFactAttribute : FactAttribute
    {
        public LiveApiFactAttribute()
        {
            if (Environment.GetEnvironmentVariable("RUN_LIVE_API_TESTS") != "true" || IsRunningInCI)
            {
                Skip = "Live API tests are skipped by default. Set RUN_LIVE_API_TESTS=true to run.";
            }

            Timeout = 30000;
        }
    }

    /// <summary>
    /// Fact attribute that skips Neo Express integration tests unless explicitly enabled.
    /// </summary>
    public class NeoExpressFactAttribute : FactAttribute
    {
        public NeoExpressFactAttribute()
        {
            if (Environment.GetEnvironmentVariable("RUN_NEO_EXPRESS_TESTS") != "true" || IsRunningInCI)
            {
                Skip = "Neo Express integration tests are skipped by default. Set RUN_NEO_EXPRESS_TESTS=true to run.";
            }

            Timeout = 30000;
        }
    }
}
