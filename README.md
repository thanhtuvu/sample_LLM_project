# sample_LLM_project

## add Docker volume so data survives container restarts:
docker rm -f elasticsearch

docker run -d \
    --name elasticsearch \
    -p 9200:9200 \
    -e "discovery.type=single-node" \
    -e "xpack.security.enabled=false" \
    -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" \
    -v elasticsearch_data:/usr/share/elasticsearch/data \
    docker.elastic.co/elasticsearch/elasticsearch:8.13.0

## .devcontainer/devcontainer.json
this file automate the manual 'docker start elasticsearch' every time your Codespace wakes up

