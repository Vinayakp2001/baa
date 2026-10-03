# Push all n8n workflow JSONs to the running n8n instance via REST API
# Maps workflow name -> ID from the current n8n DB

$idMap = @{
    "enrich-directors"              = "CC22iIsm3pl6F69i"
    "enrich-orgbook"                = "lxChQKeVXB4HAiSl"
    "ingest-bc-indigenous"          = "v33PlhIcD8g5hupW"
    "ingest-calgary"                = "YA6R2QF2F9EF4MeU"
    "ingest-corporations-canada-csv"  = "rYtXSXgnXvTRa4OS"
    "ingest-corporations-canada-html" = "DXOWmFpMxRDpFiRB"
    "ingest-edmonton"               = "zjcqTBe3BPPO97WB"
    "ingest-manitoba-weekly-pdf"    = "eaIEGG6JJDXQrgQx"
    "ingest-montreal-commercial"    = "1gvw4MsRmi9Pqvej"
    "ingest-ontario-csbif"          = "tbKZztxSQVA3eZ2J"
    "ingest-ontario-dairy"          = "Hh15rIA9YdcSEzXk"
    "ingest-ontario-dairy-plants"   = "XJ0UxKeZha5YJLKB"
    "ingest-ontario-fuel"           = "OIaifDvBighJMkXz"
    "ingest-ontario-meat"           = "tsaxJtRDG1n2QF6T"
    "ingest-ontario-select-licence" = "buQp7bjNzUouhmkb"
    "ingest-ontario-tobacco"        = "oIgz4EbtSy9zTmdK"
    "ingest-quebec-city-permits"    = "Q3O7Ejlgsela8wih"
    "ingest-saskatoon-all-biz"      = "X1dq78rpsizhTQ34"
    "ingest-saskatoon-new-biz"      = "c1RiYUjuLYQ5OUtW"
    "ingest-source"                 = "M3VpN32lUuH3n5fX"
    "ingest-source-error-handler"   = "FI0JgWc225VH9SWj"
    "ingest-vancouver"              = "3HhzSzBwMaRwFPoe"
    "ingest-winnipeg"               = "TVVt5znyNUy03pdk"
}

$workflowDir = "n8n/workflows"
$baseUrl = "http://localhost/n8n/rest/workflows"

foreach ($entry in $idMap.GetEnumerator()) {
    $name = $entry.Key
    $id   = $entry.Value

    # Find the matching JSON file
    $file = Get-ChildItem -Path $workflowDir -Filter "$name.json" | Select-Object -First 1
    if (-not $file) {
        Write-Warning "  SKIP  $name — no JSON file found"
        continue
    }

    $body = Get-Content $file.FullName -Raw | ConvertFrom-Json
    # Ensure the id field matches the DB row
    if ($body.PSObject.Properties['id']) {
        $body.id = $id
    } else {
        $body | Add-Member -NotePropertyName 'id' -NotePropertyValue $id -Force
    }

    $json = $body | ConvertTo-Json -Depth 20

    try {
        $result = Invoke-RestMethod -Method Put `
            -Uri "$baseUrl/$id" `
            -ContentType 'application/json' `
            -Body $json `
            -Headers @{ 'Accept' = 'application/json' }
        $nodeCount = $result.nodes.Count
        Write-Host "  OK    $name ($id) — $nodeCount nodes"
    } catch {
        Write-Warning "  FAIL  $name ($id) — $($_.Exception.Message)"
    }
}

Write-Host "`nDone."
