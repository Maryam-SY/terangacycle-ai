// Généré par scripts/gen-api-types.mjs depuis src/api/openapi.json : ne pas modifier.
// Régénérer : `uv run python scripts/export_openapi.py` (backend/), puis `npm run api:types`.

export interface paths {
    "/healthz": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Healthz
         * @description Vivacité : 200 tant que le processus répond, sans aucune dépendance.
         */
        get: operations["healthz_healthz_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/readyz": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Readyz
         * @description Prêt : base, Valkey, bucket et battement du worker répondent.
         */
        get: operations["readyz_readyz_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/config": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Public Config */
        get: operations["get_public_config_v1_config_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/reports": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Envoyer un Signalement */
        post: operations["create_report_v1_reports_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        /**
         * ActiveZone
         * @description Zone active publiée par `GET /v1/config` : polygone simplifié, élargi de 50 m.
         */
        ActiveZone: {
            /** Id */
            id: string;
            /** Name */
            name: string;
            geometry: components["schemas"]["MultiPolygon"];
        };
        /** Body_create_report_v1_reports_post */
        Body_create_report_v1_reports_post: {
            /** @description Métadonnées en JSON : client_uuid, lat, lng, accuracy_m, heap_size, comment, waste_type, captured_at, consent {terms, training}. */
            meta: components["schemas"]["ReportMeta"];
            /**
             * Photo
             * Format: binary
             * @description Photo du dépôt : JPEG, PNG ou WebP, 1 Mo au plus.
             */
            photo: Blob;
        };
        /**
         * Env
         * @enum {string}
         */
        Env: "dev" | "demo" | "prod";
        /** ErrorBody */
        ErrorBody: {
            code: components["schemas"]["ErrorCode"];
            /** Message */
            message: string;
            /** Request Id */
            request_id: string;
        };
        /**
         * ErrorCode
         * @enum {string}
         */
        ErrorCode: "not_found" | "method_not_allowed" | "validation_error" | "internal_error" | "unsupported_media_type" | "photo_too_large" | "photo_too_many_pixels" | "photo_unreadable" | "storage_unavailable" | "invalid_device_id" | "invalid_token" | "consent_required" | "outside_active_zone" | "client_uuid_conflict";
        /**
         * ErrorResponse
         * @description Enveloppe unique de toute réponse d'erreur.
         */
        ErrorResponse: {
            error: components["schemas"]["ErrorBody"];
        };
        /**
         * MultiPolygon
         * @description Géométrie GeoJSON (RFC 7946) : polygones → anneaux → positions [longitude, latitude].
         */
        MultiPolygon: {
            /**
             * Type
             * @constant
             */
            type: "MultiPolygon";
            /** Coordinates */
            coordinates: number[][][][];
        };
        /** PublicConfig */
        PublicConfig: {
            /** Demo Mode */
            demo_mode: boolean;
            env: components["schemas"]["Env"];
            /** Model Version */
            model_version: string | null;
            active_zone: components["schemas"]["ActiveZone"];
            /** Report Accuracy Flag M */
            report_accuracy_flag_m: number;
        };
        /**
         * ReportCreated
         * @description Réponse 201, et 200 d'un renvoi (story 1.12) : exactement ces champs. Ni
         *     `owner_key`, ni empreinte, ni Identifiant d'appareil, ni Organisation responsable.
         */
        ReportCreated: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Tracking Number */
            tracking_number: string;
            status: components["schemas"]["ReportStatus"];
            /**
             * Received At
             * Format: date-time
             */
            received_at: string;
            /** Is Demo */
            is_demo: boolean;
        };
        /**
         * ReportStatus
         * @description Statut d'un Signalement (AD-3).
         * @enum {string}
         */
        ReportStatus: "pending_review" | "validated" | "assigned" | "collected" | "rejected";
        /**
         * HeapSize
         * @description Taille de tas, obligatoire sur chaque Signalement.
         * @enum {string}
         */
        HeapSize: "small" | "medium" | "large";
        /**
         * ReportConsent
         * @description Consentements donnés sur l'appareil (AD-24).
         */
        ReportConsent: {
            /**
             * Terms
             * @default null
             */
            terms?: boolean | null;
            /** Training */
            training: boolean;
        };
        /**
         * WasteType
         * @description Type de déchet ; l'ordre est celui des classes du Modèle (AD-7).
         * @enum {string}
         */
        WasteType: "plastic" | "metal" | "glass" | "organic" | "mixed";
        /**
         * ReportMeta
         * @description Métadonnées d'un Signalement. `captured_at` (heure de l'appareil) est gardée à part
         *     et ne sert jamais à décider : le serveur date la réception par `core.clock`.
         */
        ReportMeta: {
            /**
             * Client Uuid
             * Format: uuid4
             */
            client_uuid: string;
            /** Lat */
            lat: number;
            /** Lng */
            lng: number;
            /** Accuracy M */
            accuracy_m: number;
            heap_size: components["schemas"]["HeapSize"];
            /**
             * Comment
             * @default null
             */
            comment?: string | null;
            /** @default null */
            waste_type?: components["schemas"]["WasteType"] | null;
            /**
             * Captured At
             * Format: date-time
             */
            captured_at: string;
            /** @default null */
            consent?: components["schemas"]["ReportConsent"] | null;
        };
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
    healthz_healthz_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: string;
                    };
                };
            };
            /** @description Enveloppe d'erreur */
            default: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorResponse"];
                };
            };
        };
    };
    readyz_readyz_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Une dépendance n'est pas prête (aucun détail). */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Enveloppe d'erreur */
            default: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorResponse"];
                };
            };
        };
    };
    get_public_config_v1_config_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PublicConfig"];
                };
            };
            /** @description Enveloppe d'erreur */
            default: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorResponse"];
                };
            };
        };
    };
    create_report_v1_reports_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "multipart/form-data": components["schemas"]["Body_create_report_v1_reports_post"];
            };
        };
        responses: {
            /** @description Renvoi idempotent : même auteur, même `meta.client_uuid`. Le Signalement déjà enregistré (Statut actuel), sans rien écrire ; le contenu renvoyé est ignoré. */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ReportCreated"];
                };
            };
            /** @description Signalement créé, avec son Numéro de suivi. */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ReportCreated"];
                };
            };
            /** @description `invalid_device_id` : X-Device-Id absent ou invalide. */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorResponse"];
                };
            };
            /** @description `invalid_token` : en-tête Authorization présent (non vérifiable). */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorResponse"];
                };
            };
            /** @description `client_uuid_conflict` : Identifiant client déjà utilisé par un autre auteur (rien du Signalement existant n'est renvoyé). */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorResponse"];
                };
            };
            /** @description `photo_too_large` : photo de plus de 1 Mo, ou corps de plus de 2 Mio. */
            413: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorResponse"];
                };
            };
            /** @description `unsupported_media_type` : photo ni JPEG, ni PNG, ni WebP. */
            415: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorResponse"];
                };
            };
            /** @description `validation_error` (champ nommé), `consent_required`, `outside_active_zone`, `photo_too_many_pixels`, `photo_unreadable`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorResponse"];
                };
            };
            /** @description `storage_unavailable` : stockage des photos indisponible. */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorResponse"];
                };
            };
            /** @description Enveloppe d'erreur */
            default: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorResponse"];
                };
            };
        };
    };
}
