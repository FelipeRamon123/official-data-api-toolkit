let
    // Configuration
    ApiKey = "YOUR_CENSUS_API_KEY",
    Years = {2024, 2025},
    Month = "12",
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

    GetCountries =
        (Year as number) as list =>
        let
            Response =
                Web.Contents(
                    BaseUrl,
                    [
                        RelativePath = Endpoint,
                        Query = [
                            get = "CTY_CODE,CTY_NAME,GEN_VAL_YR",
                            YEAR = Text.From(Year),
                            MONTH = Month,
                            SUMMARY_LVL = "DET",
                            SUMMARY_LVL2 = "CY",
                            key = ApiKey
                        ],
                        Timeout = #duration(0, 0, 5, 0)
                    ]
                ),

            RawTable = JsonToTable(Response),

            ValidCountries =
                Table.SelectRows(
                    RawTable,
                    each
                        [CTY_CODE] <> null
                        and [CTY_CODE] <> ""
                        and [CTY_CODE] <> "-"
                        and [CTY_NAME] <> null
                        and Int64.From([GEN_VAL_YR]) > 0
                ),

            DistinctCountries =
                Table.Distinct(
                    Table.SelectColumns(
                        ValidCountries,
                        {"CTY_CODE", "CTY_NAME"}
                    ),
                    {"CTY_CODE"}
                ),

            Output = List.Buffer(Table.ToRecords(DistinctCountries))
        in
            Output,

    QueryCountry =
        (Year as number, CountryCode as text, CountryName as text) as table =>
        let
            Response =
                Web.Contents(
                    BaseUrl,
                    [
                        RelativePath = Endpoint,
                        Query = [
                            get =
                                "I_COMMODITY,"
                                & "GEN_VAL_YR,"
                                & "CON_VAL_YR,"
                                & "DUT_VAL_YR,"
                                & "CAL_DUT_YR",
                            YEAR = Text.From(Year),
                            MONTH = Month,
                            CTY_CODE = CountryCode,
                            COMM_LVL = "HS10",
                            SUMMARY_LVL = "DET",
                            SUMMARY_LVL2 = "HSCY",
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
                        {"GEN_VAL_YR", "general_imports_usd"},
                        {"CON_VAL_YR", "imports_for_consumption_usd"},
                        {"DUT_VAL_YR", "dutiable_value_usd"},
                        {"CAL_DUT_YR", "calculated_duties_usd"}
                    }
                ),

            WithYear = Table.AddColumn(Renamed, "year", each Year, Int64.Type),
            WithCountryCode = Table.AddColumn(WithYear, "country_code", each CountryCode, type text),
            WithCountryName = Table.AddColumn(WithCountryCode, "country_name", each CountryName, type text),

            Reordered =
                Table.ReorderColumns(
                    WithCountryName,
                    {
                        "year",
                        "country_code",
                        "country_name",
                        "htsus10",
                        "general_imports_usd",
                        "imports_for_consumption_usd",
                        "dutiable_value_usd",
                        "calculated_duties_usd"
                    }
                )
        in
            Reordered,

    QueryYear =
        (Year as number) as table =>
        let
            Countries = GetCountries(Year),
            Tables =
                List.Transform(
                    Countries,
                    each QueryCountry(
                        Year,
                        Text.From([CTY_CODE]),
                        Text.From([CTY_NAME])
                    )
                ),
            Output = Table.Combine(Tables)
        in
            Output,

    TablesByYear = List.Transform(Years, each QueryYear(_)),
    Result = Table.Combine(TablesByYear)
in
    Result
