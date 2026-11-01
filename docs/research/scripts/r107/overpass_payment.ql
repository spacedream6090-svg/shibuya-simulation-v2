[out:json][timeout:120];
area["boundary"="administrative"]["name"="渋谷区"]["admin_level"="7"]->.a;
(
  nwr["tourism"~"^(hotel|hostel|guest_house|motel|apartment)$"](area.a);
  nwr[~"^payment:"~"."](area.a);
);
out tags center;
