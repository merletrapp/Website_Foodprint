from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Food
from .serializers import FoodSerializer
from decimal import Decimal


@api_view(["GET", "POST"])
def foods(request):
    if request.method == "GET":
        query = request.query_params.get("q")

        if query:
            foods = Food.objects.filter(name__icontains=query).order_by("name")
        else:
            foods = Food.objects.all()

        serializer = FoodSerializer(foods, many=True)
        return Response(serializer.data)

    if request.method == "POST":
        serializer = FoodSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


@api_view(["GET", "POST", "DELETE"])
def food(request, id):
    try:
        food = Food.objects.get(id=id)
    except:
        return Response({"detail": "not found"}, status=404)

    if request.method == "GET":
        serializer = FoodSerializer(food)
        return Response(serializer.data)

    if request.method == "POST":
        serializer = FoodSerializer(food, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

    if request.method == "DELETE":
        food.delete()
        return Response(status=204)

@api_view(["POST"])
def foods_calculate(request):
    """
    POST /api/foods/calculate/
    Body:
    {
      "items": [
        {"food_id": 1, "amount": 250, "unit": "g"},
        {"food_id": 3, "amount": 0.5, "unit": "kg"},
        {"food_id": 8, "amount": 500, "unit": "ml"},
        {"food_id": 9, "amount": 1.2, "unit": "l"}
      ]
    }

    Model:
    - Food.co2_score: kg CO2e pro Basis-Einheit
      * base_unit="kg" => pro kg
      * base_unit="l"  => pro Liter
    """
    items = request.data.get("items", [])
    if not isinstance(items, list) or len(items) == 0:
        return Response({"detail": "items muss eine nicht-leere Liste sein."}, status=400)

    total_co2 = Decimal("0.0")
    details = []

    for it in items:
        try:
            food_id = int(it.get("food_id"))
            amount = Decimal(str(it.get("amount")))
            unit = str(it.get("unit", "")).lower().strip()
        except Exception:
            return Response({"detail": "Ungültiges Item-Format."}, status=400)

        if amount <= 0:
            return Response({"detail": "amount muss > 0 sein."}, status=400)

        try:
            food = Food.objects.get(id=food_id)
        except Food.DoesNotExist:
            return Response({"detail": f"Food mit ID {food_id} nicht gefunden."}, status=404)

        # Umrechnung auf Basis-Einheit
        # - g -> kg
        # - kg -> kg
        # - ml -> l
        # - l -> l
        if unit == "g":
            amount_base = amount / Decimal("1000")
            unit_base = "kg"
        elif unit == "kg":
            amount_base = amount
            unit_base = "kg"
        elif unit == "ml":
            amount_base = amount / Decimal("1000")
            unit_base = "l"
        elif unit == "l":
            amount_base = amount
            unit_base = "l"
        else:
            return Response({"detail": f"Unbekannte Einheit: {unit}"}, status=400)

        # Einheit muss zum Food passen (fest vs. flüssig)
        if unit_base != food.base_unit:
            return Response(
                {
                    "detail": (
                        f"Einheit passt nicht zu {food.name}. "
                        f"Erwartet Basis '{food.base_unit}', bekommen '{unit_base}'."
                    )
                },
                status=400,
            )

        # co2_score ist kg CO2e pro Basis-Einheit (kg oder l)
        co2 = food.co2_score * amount_base
        total_co2 += co2

        details.append(
            {
                "food_id": food.id,
                "food": food.name,
                "amount": float(amount),              
                "unit": unit,
                "amount_base": float(amount_base),     
                "base_unit": food.base_unit,
                "co2_per_base_unit": float(food.co2_score),
                "co2": float(co2),
            }
        )

    return Response(
        {
            "total_co2": float(total_co2),
            "items": details,
        },
        status=200,
    )