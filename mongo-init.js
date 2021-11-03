db = db.getSiblingDB('clinical_backend_2');
db.createUser(
        {
            user: "idsn",
            pwd: "ökkjsdvlkadslcik83kjsbd89",
            roles: [
                {
                    role: "readWrite",
                    db: "clinical_backend_2"
                }
            ]
        }
);
 