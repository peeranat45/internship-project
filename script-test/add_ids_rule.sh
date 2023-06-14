curl -H 'Content-Type: application/json' -d '{
    "command" : [
    {
        "app" : "ids_app",
        "op" : "del",
        "src_addr" : "fd00:0:14::2"
    }
    ]
}' -d ''