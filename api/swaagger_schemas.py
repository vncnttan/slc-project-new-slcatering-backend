from drf_yasg import openapi


get_user_schema = {
    'method'        :'get',
    'security'      : [{'Bearer': []}],
    'operation_description' : "Retrieve specific user data based on the Authorization Token.",
    'manual_parameters' : [
        openapi.Parameter(
            name='all',
            in_ = openapi.IN_QUERY,
            type=openapi.TYPE_BOOLEAN,
            description="Get all users parameter",
            required=False
        ),
    ],
    'responses': {
        200: openapi.Response(
            description="Successful response",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'id': openapi.Schema(type=openapi.TYPE_STRING),
                    'username': openapi.Schema(type=openapi.TYPE_STRING),
                    'role': openapi.Schema(type=openapi.TYPE_STRING),
                    'store_name': openapi.Schema(type=openapi.TYPE_STRING),
                    'total_order': openapi.Schema(type=openapi.TYPE_INTEGER, read_only=True),
                }
            )
        ),
        500: "Internal server error",
    }
}

delete_user_schema = {
    'method':'delete',
    'security':[{'Bearer': []}],
    'request_body':openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'user_id': openapi.Schema(type=openapi.TYPE_STRING, description="User id to be deleted")
        },
        required=['user_id']
    ),
    'responses':{
        200: "Successful response",
        406: "You cannot delete your own account",
        404: "User does not exist",
        500: "Internal server error",
    }
}


get_leaderboard_schema = {
    'method':'get',
    'operation_description':"Retrieve leaderboard data for either popular caterings or top customers.",
    'manual_parameters':[
        openapi.Parameter(
            name='menu',
            in_=openapi.IN_QUERY,
            type=openapi.TYPE_BOOLEAN,
            description="If true, returns popular caterings. If false or not provided, returns top customers.",
            required=False
        ),
    ],
    'responses':{
        200: openapi.Response(
            description="Successful response",
            schema=openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    oneOf=[
                        openapi.Schema(
                            type=openapi.TYPE_OBJECT, 
                            properties={
                                # For caterings:
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'title': openapi.Schema(type=openapi.TYPE_STRING),
                                'imageLink': openapi.Schema(type=openapi.TYPE_STRING),
                                'price': openapi.Schema(type=openapi.TYPE_NUMBER),
                                'is_closed': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                'stock': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'date': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                                'created_by': openapi.Schema(type=openapi.TYPE_OBJECT),  # Serializer can define this
                                'catering_variants': openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                            'variant_name': openapi.Schema(type=openapi.TYPE_STRING),
                                            'additional_price': openapi.Schema(type=openapi.TYPE_NUMBER),
                                        }
                                    )
                                ),
                           }
                        ),
                        openapi.Schema(
                            # For users:
                            type=openapi.TYPE_OBJECT, 
                            properties={
                               'username': openapi.Schema(type=openapi.TYPE_STRING),
                               'total_order': openapi.Schema(type=openapi.TYPE_INTEGER),
                           }
                        )
                    ]
                )
            )
        ),
        500: "Internal server error",
    }
}


login_schema = {
    'method':'post',
    'request_body':openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'username': openapi.Schema(type=openapi.TYPE_STRING, description="Username for login"),
            'password': openapi.Schema(type=openapi.TYPE_STRING, description="Password for login")
        },
        required=['username', 'password']
    ),
    'responses':{
        200: openapi.Response(
            description="Successful response",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'access_token': openapi.Schema(type=openapi.TYPE_STRING, description="JWT access token"),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description="Success message")
                }
            )
        ),
        400: "Bad request",
        500: "Internal server error",
    }
}

get_catering_schema = {
    'method':'get',
    'manual_parameters':[
        openapi.Parameter(
            name="active",
            in_=openapi.IN_QUERY,
            type=openapi.TYPE_BOOLEAN,
            description="Get active caterings",
            required=True
        )
    ],
    'responses':{
        200 : "Succesfull response",
        401 : "Access denied",
        500 : "Unexpected error"       
    }
}

create_catering_schema = {
    'method':"post",
    'request_body':openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "title" : openapi.Schema(type=openapi.TYPE_STRING, description="Catering title"),
            "price" : openapi.Schema(type=openapi.TYPE_INTEGER, description="Price"),
            "stock" : openapi.Schema(type=openapi.TYPE_INTEGER, description="Catering maximum order"),
            "catering_variants" : openapi.Schema(
                type=openapi.TYPE_ARRAY,
                description="Catering variants",
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "variant_name" : openapi.Schema(type=openapi.TYPE_STRING, description="Catering variant name"),
                        "additional_price": openapi.Schema(type=openapi.TYPE_INTEGER, description="Catering variant extra price")
                    }
                ),
                required=["variant_name", "additional_price"]
            ),
        },
        required=["name", "price", "stock", "date", "catering_variants"]
    ),
    'responses':{
        201 : "Succesfully created catering",
        400 : "Bad request",
        401 : "Not authorized",
        406 : "Failed to process data",
        500 : "Unexpected error"
    }
}

close_catering_schema = {
    'method':"patch",
    'operation_description':(
        "Close catering. "
        "This endpoint will ask for catering id and will close it. "
        "It will also validate that the catering can be closed only by its creator."
    ),
    'request_body':openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "catering_id" : openapi.Schema(type=openapi.TYPE_STRING, description="Catering id to be closed")
        },
        required=['catering_id']
    ),
    'responses':{
        200 : "Sucesfully closed catering",
        404 : "Catering not found",
        500 : "Unexpected error"
    }
}