select * from deliveries
left join deliveries_assets da on da.uuid_delivery_em_infra = deliveries.uuid_em_infra
left join assets on da.uuid_asset = assets.uuid
where deliveries.referentie like 'DA-2025-52411%';


DELETE FROM assets
WHERE uuid IN (
	select assets.uuid from assets
	left join deliveries_assets da on da.uuid_asset = assets.uuid
	left join deliveries on da.uuid_delivery_em_infra = deliveries.uuid_em_infra
	where deliveries.referentie like 'DA-2025-52411%'
);


DELETE FROM deliveries_assets
WHERE uuid_delivery_em_infra IN (
	select deliveries_assets.uuid_delivery_em_infra from deliveries_assets
	left join deliveries on deliveries_assets.uuid_delivery_em_infra = deliveries.uuid_em_infra
	where deliveries.referentie like 'DA-2025-52411%'
);


DELETE FROM deliveries
where referentie like 'DA-2025-52411%';
