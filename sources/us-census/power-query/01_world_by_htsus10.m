let
    // Configuration
    ApiKey = "YOUR_CENSUS_API_KEY",
    Years = {2024, 2025},
    Month = "12",
    BaseUrl = "https://api.census.gov",
    Endpoint = "data/timeseries/intltrade/imports/hs",

    // Convert the Census JSON array into a table
    JsonToTable =
        (Content as binary) as table =>
        let
            Data = Json.Document(Content),
            Headers = Data{0},
            Rows = List.Skip(Data, 1),
            Output = Table.FromRows(Rows, Headers)
        in
            Output,

    // Query one full year. Month 12 + *_YR fields returns the year-to-date total through December.
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
                                & "I_COMMODITY_LDESC,"
                                & "GEN_VAL_YR,"
                                & "CON_VAL_YR,"
                                & "DUT_VAL_YR,"
                                & "CAL_DUT_YR",
                            YEAR = Text.From(Year),
                            MONTH = Month,
                            COMM_LVL = "HS10",
                            SUMMARY_LVL2 = "HS",
                            key = ApiKey
                        ],
                        Timeout = #duration(0, 0, 10, 0)
                    ]
                ),

            RawTable = JsonToTable(Response),

            SelectedColumns =
                Table.SelectColumns(
                    RawTable,
                    {
                        "I_COMMODITY",
                        "I_COMMODITY_LDESC",
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
                        {"I_COMMODITY_LDESC", "hts_description"},
                        {"GEN_VAL_YR", "general_imports_usd"},
                        {"CON_VAL_YR", "imports_for_consumption_usd"},
                        {"DUT_VAL_YR", "dutiable_value_usd"},
                        {"CAL_DUT_YR", "calculated_duties_usd"}
                    }
                ),

            WithYear = Table.AddColumn(Renamed, "year", each Year, Int64.Type),
            WithOrigin = Table.AddColumn(WithYear, "origin_aggregation", each "WORLD", type text),

            Reordered =
                Table.ReorderColumns(
                    WithOrigin,
                    {
                        "year",
                        "origin_aggregation",
                        "htsus10",
                        "hts_description",
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
