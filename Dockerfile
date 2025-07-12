# Neo N3 Price Feed - Production Docker Image
FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS base
WORKDIR /app
EXPOSE 8080

# Build stage
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

# Copy project files
COPY ["src/PriceFeed.Console/PriceFeed.Console.csproj", "src/PriceFeed.Console/"]
COPY ["src/PriceFeed.Core/PriceFeed.Core.csproj", "src/PriceFeed.Core/"]
COPY ["src/PriceFeed.Infrastructure/PriceFeed.Infrastructure.csproj", "src/PriceFeed.Infrastructure/"]
COPY ["src/PriceFeed.Contracts/PriceFeed.Contracts.csproj", "src/PriceFeed.Contracts/"]

# Restore dependencies
RUN dotnet restore "src/PriceFeed.Console/PriceFeed.Console.csproj"

# Copy source code
COPY . .

# Build application
WORKDIR "/src/src/PriceFeed.Console"
RUN dotnet build "PriceFeed.Console.csproj" -c Release -o /app/build

# Publish stage
FROM build AS publish
RUN dotnet publish "PriceFeed.Console.csproj" -c Release -o /app/publish /p:UseAppHost=false

# Final stage
FROM base AS final
WORKDIR /app
COPY --from=publish /app/publish .

# Create non-root user for security
RUN groupadd -r pricefeeder && useradd -r -g pricefeeder pricefeeder
RUN chown -R pricefeeder:pricefeeder /app
USER pricefeeder

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Default command
ENTRYPOINT ["dotnet", "PriceFeed.Console.dll"]