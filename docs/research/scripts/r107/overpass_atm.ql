[out:json][timeout:120];
area["boundary"="administrative"]["name"="渋谷区"]["admin_level"="7"]->.a;
(
  nwr["amenity"="atm"](area.a);
  nwr["atm"="yes"](area.a);
  nwr["amenity"="bank"](area.a);
  nwr["shop"="convenience"](area.a);
  nwr["amenity"="post_office"](area.a);
);
out tags center;
