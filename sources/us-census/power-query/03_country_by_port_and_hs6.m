let
    // ============================================================
    // CONFIGURATION
    // ============================================================

    ApiKey = "YOUR_CENSUS_API_KEY",

    // Add or remove years as needed.
    Years = {2024, 2025},

    // Select one Census Schedule C country code.
    // Example: 3510 = Brazil.
    // This example intentionally runs one country at a time because
    // Country × Port × HS6 for all countries can become extremely large.
    CountryCode = "3510",

    Month = "12",

    BaseUrl = "https://api.census.gov",
    Endpoint = "data/timeseries/intltrade/imports/porths",

    // ============================================================
    // HELPER: CENSUS JSON -> TABLE
    // ============================================================

    JsonToTable =
        (Content as binary) as table =>
        let
            Data = Json.Document(Content),
            Headers = Data{0},
            Rows = List.Skip(Data, 1),
            Output = Table.FromRows(Rows, Headers)
        in
            Output,

    // ============================================================
    // QUERY ONE YEAR FOR THE SELECTED COUNTRY
    // ============================================================

    QueryYear =
        (Year as number) as table =>
        let
            Response =
                Web.Contents(
                    BaseUrl,
                    [
                        RelativePath = Endpoint,
                        Query = [
                            // CTY_CODE is not repeated in `get` because it is
                            // already used as a predicate below.
                            get =
                                "I_COMMODITY,"
                                & "I_COMMODITY_LDESC,"
                                & "PORT,"
                                & "PORT_NAME,"
                                & "CTY_NAME,"
                                & "GEN_VAL_YR,"
                                & "AIR_VAL_YR,"
                                & "VES_VAL_YR,"
                                & "CNT_VAL_YR",

                            YEAR = Text.From(Year),
                            MONTH = Month,
                            CTY_CODE = CountryCode,
                            COMM_LVL = "HS6",
                            SUMMARY_LVL = "DET",
                            SUMMARY_LVL2 = "HSPTCY",
                            key = ApiKey
                        ],
                        Timeout = #duration(0, 0, 15, 0)
                    ]
                ),

            RawTable = JsonToTable(Response),

            SelectedColumns =
                Table.SelectColumns(
                    RawTable,
                    {
                        "CTY_CODE",
                        "CTY_NAME",
                        "PORT",
                        "PORT_NAME",
                        "I_COMMODITY",
                        "I_COMMODITY_LDESC",
                        "GEN_VAL_YR",
                        "AIR_VAL_YR",
                        "VES_VAL_YR",
                        "CNT_VAL_YR"
                    }
                ),

            Hs6Only =
                Table.SelectRows(
                    SelectedColumns,
                    each
                        [I_COMMODITY] <> null
                        and Text.Length(Text.From([I_COMMODITY])) = 6
                ),

            Typed =
                Table.TransformColumns(
                    Hs6Only,
                    {
                        {"CTY_CODE", each Text.PadStart(Text.From(_), 4, "0"), type text},
                        {"PORT", each Text.PadStart(Text.From(_), 4, "0"), type text},
                        {"I_COMMODITY", each Text.PadStart(Text.From(_), 6, "0"), type text},
                        {"GEN_VAL_YR", each Int64.From(_), Int64.Type},
                        {"AIR_VAL_YR", each Int64.From(_), Int64.Type},
                        {"VES_VAL_YR", each Int64.From(_), Int64.Type},
                        {"CNT_VAL_YR", each Int64.From(_), Int64.Type}
                    }
                ),

            Renamed =
                Table.RenameColumns(
                    Typed,
                    {
                        {"CTY_CODE", "country_code"},
                        {"CTY_NAME", "country_name"},
                        {"PORT", "port_code"},
                        {"PORT_NAME", "port_name"},
                        {"I_COMMODITY", "hs6"},
                        {"I_COMMODITY_LDESC", "hs_description"},
                        {"GEN_VAL_YR", "general_imports_usd"},
                        {"AIR_VAL_YR", "air_value_usd"},
                        {"VES_VAL_YR", "vessel_value_usd"},
                        {"CNT_VAL_YR", "containerized_vessel_value_usd"}
                    }
                ),

            WithYear =
                Table.AddColumn(
                    Renamed,
                    "year",
                    each Year,
                    Int64.Type
                ),

            Reordered =
                Table.ReorderColumns(
                    WithYear,
                    {
                        "year",
                        "country_code",
                        "country_name",
                        "port_code",
                        "port_name",
                        "hs6",
                        "hs_description",
                        "general_imports_usd",
                        "air_value_usd",
                        "vessel_value_usd",
                        "containerized_vessel_value_usd"
                    }
                )
        in
            Reordered,

    Tables = List.Transform(Years, each QueryYear(_)),
    Result = Table.Combine(Tables)
in
    Result
