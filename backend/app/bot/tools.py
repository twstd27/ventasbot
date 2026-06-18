TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "consultar_stock",
            "description": (
                "Consulta la disponibilidad y precio de uno o más productos del catálogo del comerciante. "
                "Úsalo cuando el cliente pregunte si hay stock de algún producto."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Nombre o descripción del producto a buscar",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crear_pedido",
            "description": (
                "Crea un pedido con los productos confirmados por el cliente. "
                "Úsalo solo cuando el cliente haya confirmado explícitamente qué quiere comprar y en qué cantidad."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "product_id": {"type": "string"},
                                "quantity": {"type": "integer"},
                            },
                            "required": ["product_id", "quantity"],
                        },
                    },
                },
                "required": ["items"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "obtener_info_negocio",
            "description": (
                "Obtiene información del negocio: horario de atención, ubicación, teléfono. "
                "Úsalo cuando el cliente pregunte sobre el negocio."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]
