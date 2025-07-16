# Build stage
FROM mcr.microsoft.com/dotnet/sdk:9.0 AS build
WORKDIR /src

# Copy solution and project files
COPY PriceFeed.CI.sln .
COPY src/PriceFeed.Core/*.csproj ./src/PriceFeed.Core/
COPY src/PriceFeed.Infrastructure/*.csproj ./src/PriceFeed.Infrastructure/
COPY src/PriceFeed.Console/*.csproj ./src/PriceFeed.Console/
COPY src/PriceFeed.ContractDeployer/*.csproj ./src/PriceFeed.ContractDeployer/
COPY test/PriceFeed.Tests/*.csproj ./test/PriceFeed.Tests/

# Restore dependencies
RUN dotnet restore PriceFeed.CI.sln

# Copy source code
COPY src/ ./src/
COPY test/ ./test/

# Build the application
RUN dotnet publish src/PriceFeed.Console/PriceFeed.Console.csproj \
    -c Release \
    -o /app/publish \
    --no-restore

# Runtime stage
FROM mcr.microsoft.com/dotnet/runtime:9.0-alpine AS runtime
WORKDIR /app

# Install Python for initialization scripts
RUN apk add --no-cache python3 py3-pip && \
    pip3 install requests

# Copy published application
COPY --from=build /app/publish .

# Copy scripts
COPY scripts/*.py /scripts/

# Copy configuration
COPY src/PriceFeed.Console/appsettings.json .
COPY src/PriceFeed.Console/appsettings.Production.json* .

# Create non-root user
RUN adduser -D -u 1000 pricefeed && \
    chown -R pricefeed:pricefeed /app /scripts

USER pricefeed

# Set environment
ENV DOTNET_ENVIRONMENT=Production
ENV ASPNETCORE_ENVIRONMENT=Production

# Entry point
ENTRYPOINT ["dotnet", "PriceFeed.Console.dll"]