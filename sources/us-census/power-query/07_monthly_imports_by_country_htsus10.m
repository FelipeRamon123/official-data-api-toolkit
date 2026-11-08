let
    ApiKey = "YOUR_CENSUS_API_KEY",
    CountryCode = "3510",
    StartMonth = #date(2025, 1, 1),
    EndMonth = Date.StartOfMonth(Date.AddMonths(Date.From(DateTime.LocalNow()), -1)),
    MonthCount = (Date.Year(EndMonth) - Date.Year(StartMonth)) * 12 + Date.Month(EndMonth) - Date.Month(StartMonth) + 1,
    Months = List.Transform({0..MonthCount - 1}, each Date.AddMonths(StartMonth, _)),
    BaseUrl = "https://api.census.gov",
    Endpoint = "data/timeseries/intltrade/imports/hs",
    QueryMonth = (Period as date) as table =>
        let
            Data = Json.Document(Web.Contents(BaseUrl, [RelativePath = Endpoint, Query = [
                get = "I_COMMODITY,I_COMMODITY_LDESC,CTY_NAME,GEN_VAL_MO,CON_VAL_MO,DUT_VAL_MO,CAL_DUT_MO,GEN_QY1_MO,GEN_QY2_MO,CON_QY1_MO,CON_QY2_MO,UNIT_QY1,UNIT_QY2",
                YEAR = Text.From(Date.Year(Period)), MONTH = Text.PadStart(Text.From(Date.Month(Period)), 2, "0"),
                CTY_CODE = CountryCode, COMM_LVL = "HS10", SUMMARY_LVL = "DET", SUMMARY_LVL2 = "HSCY", key = ApiKey
            ], Timeout = #duration(0, 0, 15, 0)])),
            Raw = Table.FromRows(List.Skip(Data, 1), Data{0}),
            Detail = Table.SelectRows(Raw, each Text.Length(Text.From([I_COMMODITY])) = 10),
            WithPeriod = Table.AddColumn(Detail, "period", each Date.ToText(Period, "yyyy-MM"), type text),
            WithCountry = Table.AddColumn(WithPeriod, "country_code", each CountryCode, type text),
            Renamed = Table.RenameColumns(WithCountry, {
                {"I_COMMODITY", "htsus10"}, {"I_COMMODITY_LDESC", "description_en"}, {"CTY_NAME", "country_name"},
                {"GEN_VAL_MO", "general_value_usd"}, {"CON_VAL_MO", "consumption_value_usd"},
                {"DUT_VAL_MO", "dutiable_value_usd"}, {"CAL_DUT_MO", "calculated_duties_usd"},
                {"GEN_QY1_MO", "general_qty1"}, {"GEN_QY2_MO", "general_qty2"},
                {"CON_QY1_MO", "consumption_qty1"}, {"CON_QY2_MO", "consumption_qty2"},
                {"UNIT_QY1", "unit_qty1"}, {"UNIT_QY2", "unit_qty2"}
            }),
            Numeric = Table.TransformColumnTypes(Renamed, {{"general_value_usd", Int64.Type}, {"consumption_value_usd", Int64.Type}, {"dutiable_value_usd", Int64.Type}, {"calculated_duties_usd", Int64.Type}, {"general_qty1", Int64.Type}, {"general_qty2", Int64.Type}, {"consumption_qty1", Int64.Type}, {"consumption_qty2", Int64.Type}})
        in Numeric,
    Result = Table.Combine(List.Transform(Months, each QueryMonth(_)))
in
    Result
