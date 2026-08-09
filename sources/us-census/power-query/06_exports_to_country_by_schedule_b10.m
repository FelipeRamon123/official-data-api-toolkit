let
    // ============================================================
    // CONFIGURATION
    // ============================================================

    ApiKey = "YOUR_CENSUS_API_KEY",

    // Add or remove years as needed.
    Years = {2024, 2025},

    // Select one Census Schedule C destination-country code.
    // Example: 3510 = Brazil.
    CountryCode = "3510",

    Month = "12",

    BaseUrl = "https://api.census.gov",
    Endpoint = "data/timeseries/intltrade/exports/hs",

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
    // QUERY ONE YEAR FOR THE SELECTED DESTINATION COUNTRY
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
                            get =
                                "E_COMMODITY,"
                                & "E_COMMODITY_LDESC,"
                                & "DF,"
                                & "CTY_NAME,"
                                & "ALL_VAL_YR",

                            YEAR = Text.From(Year),
                            MONTH = Month,
                            CTY_CODE = CountryCode,
                            COMM_LVL = "HS10",
                            SUMMARY_LVL = "DET",
                            SUMMARY_LVL2 = "HSCYDF",
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
                        "E_COMMODITY",
                        "E_COMMODITY_LDESC",
                        "DF",
                        "CTY_NAME",
                        "ALL_VAL_YR"
                    }
                ),

            ScheduleB10Only =
                Table.SelectRows(
                    SelectedColumns,
                    each
                        [E_COMMODITY] <> null
                        and Text.Length(Text.From([E_COMMODITY])) = 10
                ),

            Typed =
                Table.TransformColumns(
                    ScheduleB10Only,
                    {
                        {"E_COMMODITY", each Text.PadStart(Text.From(_), 10, "0"), type text},
                        {"DF", each Text.From(_), type text},
                        {"ALL_VAL_YR", each Int64.From(_), Int64.Type}
                    }
                ),

            WithExportType =
                Table.AddColumn(
                    Typed,
                    "export_type",
                    each
                        if [DF] = "1" then "Domestic"
                        else if [DF] = "2" then "Foreign (re-export)"
                        else "Other",
                    type text
                ),

            Renamed =
                Table.RenameColumns(
                    WithExportType,
                    {
                        {"E_COMMODITY", "schedule_b10"},
                        {"E_COMMODITY_LDESC", "schedule_b_description"},
                        {"DF", "export_type_code"},
                        {"CTY_NAME", "country_name"},
                        {"ALL_VAL_YR", "export_value_usd"}
                    }
                ),

            WithYear =
                Table.AddColumn(
                    Renamed,
                    "year",
                    each Year,
                    Int64.Type
                ),

            WithCountryCode =
                Table.AddColumn(
                    WithYear,
                    "country_code",
                    each CountryCode,
                    type text
                ),

            Reordered =
                Table.ReorderColumns(
                    WithCountryCode,
                    {
                        "year",
                        "country_code",
                        "country_name",
                        "schedule_b10",
                        "schedule_b_description",
                        "export_type_code",
                        "export_type",
                        "export_value_usd"
                    }
                )
        in
            Reordered,

    Tables = List.Transform(Years, each QueryYear(_)),
    Result = Table.Combine(Tables)
in
    Result
