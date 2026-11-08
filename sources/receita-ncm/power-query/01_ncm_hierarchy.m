let
    SourceUrl = "https://portalunico.siscomex.gov.br/classif/api/publico/nomenclatura/download/json",
    Source = Json.Document(Web.Contents(SourceUrl)),
    Rows = Table.FromRecords(Source[Nomenclaturas]),
    Digits = Table.AddColumn(Rows, "code", each Text.Select(Text.From([Codigo]), {"0".."9"}), type text),
    SharedHS = Table.SelectRows(Digits, each List.Contains({2, 4, 6}, Text.Length([code]))),
    WithLevel = Table.AddColumn(SharedHS, "level", each "SH" & Text.From(Text.Length([code])), type text),
    Selected = Table.SelectColumns(WithLevel, {"level", "code", "Descricao"}),
    Renamed = Table.RenameColumns(Selected, {{"Descricao", "description_pt"}})
in
    Renamed
