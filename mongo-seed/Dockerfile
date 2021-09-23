FROM mongo

COPY admin.json /admin.json
CMD mongoimport --host mongodb --db DSPharmacy --collection Users --type json --file /admin.json --jsonArray