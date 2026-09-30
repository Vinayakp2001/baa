import { api } from "@/lib/api";
import { notFound } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { QualityBadge } from "@/components/QualityBadge";
import { EventTimeline } from "@/components/EventTimeline";
import { ProvenancePanel } from "@/components/ProvenancePanel";
import { DncFlagButton } from "@/components/DncFlagButton";

export const dynamic = "force-dynamic";

interface Props { params: { id: string } }

export default async function BusinessDetailPage({ params }: Props) {
  let business, history, events;
  try {
    [business, history, events] = await Promise.all([
      api.businesses.get(params.id),
      api.businesses.history(params.id),
      api.events.list({ entity_id: params.id, page_size: 50 } as Record<string, string | number | undefined>),
    ]);
  } catch {
    notFound();
  }

  const primaryLocation = business.locations.find((l) => l.is_primary) ?? business.locations[0];
  const phones = business.contacts.filter((c) => c.contact_type === "PHONE");
  const emails = business.contacts.filter((c) => c.contact_type === "EMAIL");
  const websites = business.contacts.filter((c) => c.contact_type === "WEBSITE");
  const directors = business.persons.filter((p) => p.role_type === "DIRECTOR");

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">{business.canonical_name}</h1>
          {business.legal_name && business.legal_name !== business.canonical_name && (
            <p className="text-muted-foreground text-sm">Legal: {business.legal_name}</p>
          )}
          {business.trade_name && (
            <p className="text-muted-foreground text-sm">DBA: {business.trade_name}</p>
          )}
          <div className="flex items-center gap-2 mt-2">
            {business.status && (
              <Badge variant={business.status === "ACTIVE" ? "success" : "secondary"}>
                {business.status}
              </Badge>
            )}
            {business.province && <Badge variant="outline">{business.province}</Badge>}
            {business.sales_ready && <Badge variant="success">Sales Ready</Badge>}
            <QualityBadge score={business.lead_quality_score} />
          </div>
        </div>
        <DncFlagButton entityId={business.entity_id} />
      </div>

      {/* Main tabs via CSS — server-rendered sections */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Identity */}
        <Card>
          <CardHeader><CardTitle>Identity</CardTitle></CardHeader>
          <CardContent className="space-y-2 text-sm">
            <Row label="Entity Type" value={business.entity_type} />
            <Row label="Province" value={business.province} />
            <Row label="First Seen" value={business.first_seen_at ? new Date(business.first_seen_at).toLocaleDateString("en-CA") : null} />
            <Row label="Last Verified" value={business.last_verified_at ? new Date(business.last_verified_at).toLocaleDateString("en-CA") : null} />
            {business.identifiers.map((id) => (
              <Row key={id.id_type} label={id.id_type} value={id.id_value} />
            ))}
          </CardContent>
        </Card>

        {/* Address */}
        <Card>
          <CardHeader><CardTitle>Location</CardTitle></CardHeader>
          <CardContent className="space-y-2 text-sm">
            {primaryLocation ? (
              <>
                <Row label="Address" value={primaryLocation.address_line1} />
                <Row label="City" value={primaryLocation.city} />
                <Row label="Province" value={primaryLocation.province} />
                <Row label="Postal" value={primaryLocation.postal_code} />
                {primaryLocation.latitude && (
                  <Row label="Coordinates" value={`${primaryLocation.latitude}, ${primaryLocation.longitude}`} />
                )}
              </>
            ) : (
              <p className="text-muted-foreground">No location data</p>
            )}
          </CardContent>
        </Card>

        {/* Contact */}
        <Card>
          <CardHeader><CardTitle>Contact</CardTitle></CardHeader>
          <CardContent className="space-y-3 text-sm">
            {phones.length === 0 && emails.length === 0 && websites.length === 0 ? (
              <p className="text-muted-foreground">No contact data</p>
            ) : null}
            {phones.map((c) => (
              <div key={c.contact_id} className="flex items-start justify-between">
                <div>
                  <span className="text-muted-foreground mr-2">Phone</span>
                  <span>{c.normalised_value ?? c.raw_value}</span>
                </div>
                {c.confidence && <Badge variant="outline" className="text-xs">{c.confidence}</Badge>}
              </div>
            ))}
            {emails.map((c) => (
              <div key={c.contact_id} className="flex items-start justify-between">
                <div>
                  <span className="text-muted-foreground mr-2">Email</span>
                  <a href={`mailto:${c.normalised_value}`} className="text-primary hover:underline">
                    {c.normalised_value ?? c.raw_value}
                  </a>
                </div>
                {c.confidence && <Badge variant="outline" className="text-xs">{c.confidence}</Badge>}
              </div>
            ))}
            {websites.map((c) => (
              <div key={c.contact_id} className="flex items-start justify-between">
                <div>
                  <span className="text-muted-foreground mr-2">Website</span>
                  <a href={`https://${c.normalised_value}`} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                    {c.normalised_value ?? c.raw_value}
                  </a>
                </div>
                {c.enrichment_source && <Badge variant="outline" className="text-xs">{c.enrichment_source}</Badge>}
              </div>
            ))}
          </CardContent>
        </Card>

        {/* People */}
        <Card>
          <CardHeader><CardTitle>People</CardTitle></CardHeader>
          <CardContent className="space-y-2 text-sm">
            {business.persons.length === 0 ? (
              <p className="text-muted-foreground">No people data</p>
            ) : (
              business.persons.map((p) => (
                <div key={p.person_id} className="flex items-center justify-between">
                  <span>{p.person_name}</span>
                  <Badge variant="outline" className="text-xs">{p.role_type ?? p.role_label_raw ?? "—"}</Badge>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        {/* Employees */}
        {business.employee_data.length > 0 && (
          <Card>
            <CardHeader><CardTitle>Employees</CardTitle></CardHeader>
            <CardContent className="space-y-2 text-sm">
              {business.employee_data.map((e) => (
                <div key={e.employee_id}>
                  <Row label="Raw value" value={e.raw_employee_value} />
                  <Row label="Bucket" value={e.employee_bucket} />
                  {e.employee_min !== null && (
                    <Row label="Range" value={`${e.employee_min}${e.employee_max ? ` – ${e.employee_max}` : "+"}`} />
                  )}
                  {e.data_quality_flag && (
                    <Badge variant="warning" className="text-xs">{e.data_quality_flag}</Badge>
                  )}
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Industry */}
        {business.industries.length > 0 && (
          <Card>
            <CardHeader><CardTitle>Industry</CardTitle></CardHeader>
            <CardContent className="space-y-2 text-sm">
              {business.industries.map((ind) => (
                <div key={ind.industry_id}>
                  <Row label="NAICS" value={ind.source_naics} />
                  <Row label="Sector" value={ind.naics_sector} />
                  <Row label="Description" value={ind.source_industry_str} />
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Quality Score */}
        {business.quality_score && (
          <Card>
            <CardHeader><CardTitle>Quality Score</CardTitle></CardHeader>
            <CardContent className="space-y-2 text-sm">
              {Object.entries(business.quality_score)
                .filter(([k]) => k !== "scored_at")
                .map(([k, v]) => (
                  <div key={k} className="flex items-center justify-between">
                    <span className="text-muted-foreground capitalize">{k.replace(/_/g, " ")}</span>
                    <div className="flex items-center gap-2">
                      {typeof v === "number" && (
                        <div className="w-20 h-1.5 rounded-full bg-muted overflow-hidden">
                          <div className="h-full rounded-full bg-primary" style={{ width: `${v}%` }} />
                        </div>
                      )}
                      <span className="tabular-nums w-8 text-right">{v ?? "—"}</span>
                    </div>
                  </div>
                ))}
            </CardContent>
          </Card>
        )}
      </div>

      {/* Events timeline */}
      {events && events.results.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Event Timeline</CardTitle></CardHeader>
          <CardContent>
            <EventTimeline events={events.results} />
          </CardContent>
        </Card>
      )}

      {/* Provenance */}
      {history && (
        <Card>
          <CardHeader><CardTitle>Field History</CardTitle></CardHeader>
          <CardContent>
            <ProvenancePanel history={history} />
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function Row({ label, value }: { label: string; value: string | null | undefined }) {
  if (!value) return null;
  return (
    <div className="flex items-start justify-between gap-4">
      <span className="text-muted-foreground shrink-0">{label}</span>
      <span className="text-right break-all">{value}</span>
    </div>
  );
}
