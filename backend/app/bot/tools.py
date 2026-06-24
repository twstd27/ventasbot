TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "consultar_stock",
            "description": (
                "Consulta los productos del catálogo del comerciante (nombre, precio y stock). "
                "Si el cliente pregunta por un producto específico, pasa su nombre en 'query'. "
                "Si pregunta de forma general qué hay disponible (ej. '¿qué productos tienes?', "
                "'muéstrame el catálogo'), llama SIN 'query' para ver el catálogo. "
                "El resultado puede ser parcial: si 'hay_mas' es true o 'total_coincidencias' "
                "es grande, no listes todo, muestra algunos y pide al cliente que acote por tipo/categoría. "
                "Úsalo siempre antes de afirmar qué existe o no; nunca inventes productos."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "Nombre o descripción del producto a buscar. "
                            "Omítelo o déjalo vacío para listar todo el catálogo."
                        ),
                    },
                },
                "required": [],
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
