let
    // ============================================================
    // CONFIGURATION
    // ============================================================

    ApiKey = "YOUR_CENSUS_API_KEY",
    Years = {2024, 2025},
    Month = "12",

    // Select one Census Schedule C country code.
    // Example: 3510 = Brazil.
    CountryCode = "3510",

    BaseUrl = "https://api.census.gov",
    Endpoint = "data/timeseries/intltrade/imports/hs",

    JsonToTable =
        (Content as binary) as table =>
        let
            Data = Json.Document(Content),
            Headers = Data{0},
            Rows = List.Skip(Data, 1),
            Output = Table.FromRows(Rows, Headers)
        in
            Output,

    QueryYear =
        (Year as number) as table =>
        let
            Response =
                Web.Contents(
                    BaseUrl,
                    [
                        RelativePath = Endpoint,
                        Query = [
                            get =
                                "I_COMMODITY,"
                                & "RP,"
                                & "CTY_NAME,"
                                & "GEN_VAL_YR,"
                                & "CON_VAL_YR,"
                                & "DUT_VAL_YR,"
                                & "CAL_DUT_YR",
                            YEAR = Text.From(Year),
                            MONTH = Month,
                            CTY_CODE = CountryCode,
                            COMM_LVL = "HS10",
                            SUMMARY_LVL = "DET",
                            SUMMARY_LVL2 = "HSCYRP",
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
                        "I_COMMODITY",
                        "RP",
                        "CTY_NAME",
                        "GEN_VAL_YR",
                        "CON_VAL_YR",
                        "DUT_VAL_YR",
                        "CAL_DUT_YR"
                    }
                ),

            Htsus10Only =
                Table.SelectRows(
                    SelectedColumns,
                    each
                        [I_COMMODITY] <> null
                        and Text.Length(Text.From([I_COMMODITY])) = 10
                ),

            Typed =
                Table.TransformColumns(
                    Htsus10Only,
                    {
                        {"I_COMMODITY", each Text.PadStart(Text.From(_), 10, "0"), type text},
                        {"RP", each Text.PadStart(Text.From(_), 2, "0"), type text},
                        {"GEN_VAL_YR", each Int64.From(_), Int64.Type},
                        {"CON_VAL_YR", each Int64.From(_), Int64.Type},
                        {"DUT_VAL_YR", each Int64.From(_), Int64.Type},
                        {"CAL_DUT_YR", each Int64.From(_), Int64.Type}
                    }
                ),

            Renamed =
                Table.RenameColumns(
                    Typed,
                    {
                        {"I_COMMODITY", "htsus10"},
                        {"RP", "rate_provision_code"},
                        {"CTY_NAME", "country_name"},
                        {"GEN_VAL_YR", "general_imports_usd"},
                        {"CON_VAL_YR", "imports_for_consumption_usd"},
                        {"DUT_VAL_YR", "dutiable_value_usd"},
                        {"CAL_DUT_YR", "calculated_duties_usd"}
                    }
                ),

            WithYear = Table.AddColumn(Renamed, "year", each Year, Int64.Type),
            WithCountryCode = Table.AddColumn(WithYear, "country_code", each CountryCode, type text),

            Reordered =
                Table.ReorderColumns(
                    WithCountryCode,
                    {
                        "year",
                        "country_code",
                        "country_name",
                        "htsus10",
                        "rate_provision_code",
                        "general_imports_usd",
                        "imports_for_consumption_usd",
                        "dutiable_value_usd",
                        "calculated_duties_usd"
                    }
                )
        in
            Reordered,

    Tables = List.Transform(Years, each QueryYear(_)),
    Result = Table.Combine(Tables)
in
    Result
