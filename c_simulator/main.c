#include <stdint.h>
#include <stdio.h> 
#include <stdlib.h> 
#include <string.h>
#include <curl/curl.h>
#include <unistd.h>
#include <time.h>

// Definitions des structures

typedef struct
{
    char *memory;
    size_t size;

}MemoryStruct;

typedef struct{
    uint8_t bpm; // frequence cardique entre 60 et 100
    float spO2; // saturation en oxygene entre 95.0% et 99.9%
    float temperature; // entre 36.2 et 37.5 degre celcius
}health_t;

// variables

//prototypes de fonctions

/*
@brief :
// Callback pour récapituler les morceaux HTTP reçus par cURL
* `void *contents` : le pointeur vers les nouveaux octets bruts reçus du serveur.
* `size_t size` : la taille d'un élément (toujours 1 octet).
* `size_t nmemb` : le nombre d'éléments reçus (la taille totale reçue est donc `size * nmemb`).
*/

static size_t WriteMemoryCallback(void *contents, size_t size, size_t nmemb, void *userp){

    // calcul de la taille du morceau recu
    size_t realsize = size * nmemb;

    // transtypage
    MemoryStruct *mem = (MemoryStruct *)userp;

    // reallocation de la memoire
    char *p = realloc(mem->memory, realsize+ mem->size+1);
    if(p == NULL){
        printf("Erreur : plus assez de mémoire !\n");
        return 0;
    }
    mem->memory = p;
    memcpy(&(mem->memory[mem->size]),contents, realsize);

    mem->size += realsize;
    mem->memory[mem->size] = '\0';

    return realsize;
}

int main(void){
    setbuf(stdout, NULL);

    const char *base_url;
    const char *simulator_email;
    const char *simulator_password;

    base_url = getenv("API_URL");
    simulator_email =getenv("SIMULATOR_EMAIL");
    simulator_password =getenv("SIMULATOR_PASSWORD");

    if (base_url == NULL){
        base_url = "http://backend:8000";
    }

    if (simulator_email == NULL){
        simulator_email = "anne@chrys.com";
    }
    
    if(simulator_password == NULL){
        simulator_password = "camille";
    }

    printf("Démarrage du simulateur...\n");
    printf("Serveur : %s | Utilisateur : %s\n", base_url, simulator_email);

    // Connexion
    char login_url[256];
    snprintf(login_url, sizeof(login_url), "%s/api/v1/auth/login", base_url);

    // url de telemetrie
    char telemetry_url[256];
    snprintf(telemetry_url, sizeof(telemetry_url), "%s/api/v1/telemetry/push", base_url);

    char post_data[256];
    snprintf(post_data, sizeof(post_data), "username=%s&password=%s", simulator_email, simulator_password);

    char jwt_token[512] ={0};

    CURL *curl = curl_easy_init();
    if (curl) {
        curl_easy_setopt(curl, CURLOPT_URL ,login_url);
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, post_data);
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteMemoryCallback);

        int authenticated = 0;
        while (!authenticated) {
            MemoryStruct chunk;
            chunk.memory = malloc(1);
            chunk.size = 0;
            if (chunk.memory == NULL) {
                fprintf(stderr, "Erreur : impossible d'allouer le tampon de réponse.\n");
                curl_easy_cleanup(curl);
                return EXIT_FAILURE;
            }
            chunk.memory[0] = '\0';

            curl_easy_setopt(curl, CURLOPT_WRITEDATA, (void *)&chunk);
            CURLcode res = curl_easy_perform(curl);

            if (res == CURLE_OK) {
                char *token_start = strstr(chunk.memory, "\"access_token\":\"");
                if (token_start != NULL) {
                    token_start += strlen("\"access_token\":\"");
                    char *token_end = strchr(token_start, '"');
                    if (token_end != NULL) {
                        size_t token_len = (size_t)(token_end - token_start);
                        if (token_len > 0 && token_len < sizeof(jwt_token)) {
                            memcpy(jwt_token, token_start, token_len);
                            jwt_token[token_len] = '\0';
                            printf("Connecté avec succès ! Token JWT récupéré.\n");
                            authenticated = 1;
                        }
                    }
                }
            } else {
                fprintf(stderr, "Erreur cURL lors de la connexion : %s\n",
                        curl_easy_strerror(res));
            }

            free(chunk.memory);
            if (!authenticated) {
                printf("En attente de la disponibilité du backend (/login)... nouvelle tentative dans 3s\n");
                sleep(3);
            }
        }

        // Boucle d'envoi de télémétrie en temps réel
        if (strlen(jwt_token) > 0) {
            printf("Début de l'envoi de la télémétrie...\n");

            srand(time(NULL));
            health_t data_h;
            int count = 0;
            while (1)
            {
                count++;
                if (count <= 10){
                data_h.bpm =60 +  rand()%(41);
                data_h.spO2 = 95.0 + ((float)rand() / (float)RAND_MAX) * (4.9);
                data_h.temperature = 36.2 + ((float)rand() / (float)RAND_MAX) * (37.5-36.2);
                    
                }
                else{
                data_h.bpm = 145; // Tachycardie marquée 
                data_h.spO2 = 89.0; // Hypoxie sévère 
                data_h.temperature = 38.8; // Fièvre
                }

                // json

                char json_payload[512];
                snprintf(json_payload, sizeof(json_payload), "{\"bpm\": %u, \"spo2\": %.1f, \"temperature\": %.1f, \"contexte\" : \"rest\"}", data_h.bpm, data_h.spO2, data_h.temperature);

                // jwt dans l'entete http


                struct curl_slist *headers = NULL;
                headers = curl_slist_append(headers, "Content-Type: application/json");

                char auth_header[600];
                snprintf(auth_header, sizeof(auth_header), "Authorization: Bearer %s", jwt_token);
                headers = curl_slist_append(headers, auth_header);

                // preparation du tampon de reponse

                MemoryStruct response_chunk;
                response_chunk.memory = malloc(1);
                response_chunk.size = 0;

                if (response_chunk.memory == NULL){
                    fprintf(stderr, "Erreur d'allocation memoire\n");
                    continue;
                }
                response_chunk.memory[0] = '\0';
                
                // configuration du cURL pour capturer la reponse
                
                curl_easy_setopt(curl, CURLOPT_URL, telemetry_url);
                curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
                curl_easy_setopt(curl, CURLOPT_POSTFIELDS, json_payload);

                //indication de la fonction de callback

                curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteMemoryCallback);
                curl_easy_setopt(curl, CURLOPT_WRITEDATA, (void *)&response_chunk);

                // execution de la requete http

                CURLcode tele_res = curl_easy_perform(curl);

                // analyse de la reponse du serveur
                if ( tele_res == CURLE_OK){
                    long response_code = 0;
                    curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &response_code);
                    if (response_code < 200 || response_code >= 300) {
                        fprintf(stderr, "Erreur HTTP lors de l'envoi (%ld) : %s\n",
                                response_code, response_chunk.memory);
                    }
                    else{
                        printf("Télémétrie envoyée : %s\n", json_payload);

                        if(strstr(response_chunk.memory, "\"is_anomaly\":true") != NULL || strstr(response_chunk.memory, "\"is_anomaly\": true") != NULL){
                            printf("[ALERT IOT] Anomalies détectées\n");
                            printf("Détail réponse backend : %s\n", response_chunk.memory);
                        }
                        else{
                            printf("[OK] Télémétrie enregistrée sans anomalie\n");
                        }
                    }
                }
                else{
                    fprintf(stderr, "Erreur envoi télémétrie : %s\n", curl_easy_strerror(tele_res));
                }
                // Netotyage du tampon de memoire
                free(response_chunk.memory);
                curl_slist_free_all(headers); // liberation de l'URL
                sleep(1);
            }
        }
        curl_easy_cleanup(curl);
    }   
    return 0;
}
