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
    Endpoint = "data/timeseries/intltrade/imports/sitc",

    SitcSectionName =
        (Code as text) as text =>
            if Code = "0" then "Food and live animals"
            else if Code = "1" then "Beverages and tobacco"
            else if Code = "2" then "Crude materials, inedible, except fuels"
            else if Code = "3" then "Mineral fuels, lubricants and related materials"
            else if Code = "4" then "Animal and vegetable oils, fats and waxes"
            else if Code = "5" then "Chemicals and related products"
            else if Code = "6" then "Manufactured goods classified chiefly by material"
            else if Code = "7" then "Machinery and transport equipment"
            else if Code = "8" then "Miscellaneous manufactured articles"
            else if Code = "9" then "Commodities and transactions not classified elsewhere"
            else "Unclassified",

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
                                "SITC,"
                                & "CTY_NAME,"
                                & "GEN_VAL_YR,"
                                & "CON_VAL_YR,"
                                & "DUT_VAL_YR,"
                                & "CAL_DUT_YR",
                            YEAR = Text.From(Year),
                            MONTH = Month,
                            CTY_CODE = CountryCode,
                            SUMMARY_LVL = "DET",
                            SUMMARY_LVL2 = "SICY",
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
                        "SITC",
                        "CTY_NAME",
                        "GEN_VAL_YR",
                        "CON_VAL_YR",
                        "DUT_VAL_YR",
                        "CAL_DUT_YR"
                    }
                ),

            Sitc5Only =
                Table.SelectRows(
                    SelectedColumns,
                    each [SITC] <> null and Text.Length(Text.From([SITC])) = 5
                ),

            Typed =
                Table.TransformColumns(
                    Sitc5Only,
                    {
                        {"SITC", each Text.From(_), type text},
                        {"GEN_VAL_YR", each Int64.From(_), Int64.Type},
                        {"CON_VAL_YR", each Int64.From(_), Int64.Type},
                        {"DUT_VAL_YR", each Int64.From(_), Int64.Type},
                        {"CAL_DUT_YR", each Int64.From(_), Int64.Type}
                    }
                ),

            CountryName =
                if Table.RowCount(Typed) > 0
                then Text.From(Typed{0}[CTY_NAME])
                else null,

            WithSection =
                Table.AddColumn(
                    Typed,
                    "sitc_section",
                    each Text.Start([SITC], 1),
                    type text
                ),

            Grouped =
                Table.Group(
                    WithSection,
                    {"sitc_section"},
                    {
                        {"general_imports_usd", each List.Sum([GEN_VAL_YR]), Int64.Type},
                        {"imports_for_consumption_usd", each List.Sum([CON_VAL_YR]), Int64.Type},
                        {"dutiable_value_usd", each List.Sum([DUT_VAL_YR]), Int64.Type},
                        {"calculated_duties_usd", each List.Sum([CAL_DUT_YR]), Int64.Type}
                    }
                ),

            WithSectionName =
                Table.AddColumn(
                    Grouped,
                    "sitc_section_name",
                    each SitcSectionName([sitc_section]),
                    type text
                ),

            WithYear = Table.AddColumn(WithSectionName, "year", each Year, Int64.Type),
            WithCountryCode = Table.AddColumn(WithYear, "country_code", each CountryCode, type text),
            WithCountryName = Table.AddColumn(WithCountryCode, "country_name", each CountryName, type nullable text),

            Reordered =
                Table.ReorderColumns(
                    WithCountryName,
                    {
                        "year",
                        "country_code",
                        "country_name",
                        "sitc_section",
                        "sitc_section_name",
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
