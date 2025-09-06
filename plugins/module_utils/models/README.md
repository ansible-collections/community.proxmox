wget https://raw.githubusercontent.com/LUMASERV/proxmox-ve-openapi/refs/heads/main/reference/spec.v2.yaml
pip install datamodel-codegen 
datamodel-codegen --openapi-scopes paths --use-annotated --use-title-as-name --reuse-model --input spec.v2.yaml --input-file-type openapi --output paths2.py --output-model-type pydantic_v2.BaseModel
