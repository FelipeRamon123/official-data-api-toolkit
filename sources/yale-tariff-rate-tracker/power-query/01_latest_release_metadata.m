let
    Repository = "Budget-Lab-Yale/tariff-rate-tracker",
    Response =
        Json.Document(
            Web.Contents(
                "https://api.github.com",
                [
                    RelativePath = "repos/" & Repository & "/releases/latest",
                    Headers = [Accept = "application/vnd.github+json", #"User-Agent" = "official-data-api-toolkit"]
                ]
            )
        ),
    ZipAssets = List.Select(Response[assets], each Text.EndsWith([name], ".zip")),
    Asset = if List.Count(ZipAssets) = 0 then error "The latest release has no ZIP asset." else ZipAssets{0},
    Output =
        #table(
            {"repository", "tag", "published_at", "release_url", "asset", "asset_url", "asset_size"},
            {{Repository, Response[tag_name], Response[published_at], Response[html_url], Asset[name], Asset[browser_download_url], Asset[size]}}
        )
in
    Output
