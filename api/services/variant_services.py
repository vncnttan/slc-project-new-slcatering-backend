from api.models import VariantCaterings
def get_variant_by_id(id: str):
    try:
        return VariantCaterings.objects.get(id = id)

    except VariantCaterings.DoesNotExist as e:
        return None
    