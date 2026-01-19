def main():
    trip_to_route = load_trip_to_route_map()

    print("Descargando vehículos...")
    df = fetch_vehicle_positions()
    if df.empty:
        print("No hay vehículos con lat/lon.")
        return

    alerts_by_route, alerts_by_stop = fetch_alerts()

    print("Rutas con avisos:", len(alerts_by_route))
    print("Stops con avisos:", len(alerts_by_stop))

    # Añade routeId a cada tren usando tripId
    df["routeId"] = df["tripId"].astype(str).map(trip_to_route)

    # ---- DEBUG ----
    no_route = int(df["routeId"].isna().sum())
    print("Trenes sin routeId (no cruzan GTFS):", no_route, "de", len(df))

    routes_in_trains = set(df["routeId"].dropna().astype(str).head(50).tolist())
    print("Ejemplos routeId en trenes:", list(routes_in_trains)[:10])

    routes_in_alerts = set(list(alerts_by_route.keys())[:50])
    print("Ejemplos routeId en alertas:", list(routes_in_alerts)[:10])

    inter = routes_in_trains.intersection(routes_in_alerts)
    print("INTERSECCION routeId trenes vs alertas:", len(inter))
    if inter:
        print("Ejemplo routeId que coincide:", list(inter)[:5])

    def has_any_alert(row):
        sid = str(row["stopId"]) if pd.notna(row["stopId"]) else None
        rid = str(row["routeId"]) if pd.notna(row["routeId"]) else None
        return (sid in alerts_by_stop) or (rid in alerts_by_route)

    num_with_alerts = int(df.apply(has_any_alert, axis=1).sum())
    print("Trenes con algún aviso:", num_with_alerts)
    # ---- FIN DEBUG ----

    # Centro del mapa
    m = folium.Map(location=[df["lat"].mean(), df["lon"].mean()], zoom_start=6)

    # Marcadores
    for _, r in df.iterrows():
        stop_id = str(r.get("stopId")) if pd.notna(r.get("stopId")) else None
        route_id = str(r.get("routeId")) if pd.notna(r.get("routeId")) else None

        stop_msgs = alerts_by_stop.get(stop_id, []) if stop_id else []
        route_msgs = alerts_by_route.get(route_id, []) if route_id else []
        has_alert = bool(stop_msgs or route_msgs)

        popup_lines = [
            f"<b>{r.get('label','')}</b>",
            f"status: {r.get('status','')}",
            f"tripId: {r.get('tripId','')}",
            f"routeId: {route_id or '—'}",
            f"stopId: {stop_id or '—'}",
        ]

        if route_msgs:
            popup_lines.append("<br><b>AVISOS (route):</b>")
            popup_lines += [f"- {t}" for t in route_msgs[:3]]

        if stop_msgs:
            popup_lines.append("<br><b>AVISOS (stop):</b>")
            popup_lines += [f"- {t}" for t in stop_msgs[:3]]

        popup_html = "<br>".join(popup_lines)
        popup = folium.Popup(popup_html, max_width=450)

        if has_alert:
            folium.Marker(
                location=[r["lat"], r["lon"]],
                popup=popup,
                icon=folium.Icon(icon="exclamation-sign")
            ).add_to(m)
        else:
            folium.CircleMarker(
                location=[r["lat"], r["lon"]],
                radius=4,
                popup=popup
            ).add_to(m)

    out = "trenes_renfe_osm.html"
    m.save(out)
    print("OK ->", out)