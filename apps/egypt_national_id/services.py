from apps.egypt_national_id.repos import ApiUsageRepository
from bases.business_logic import CreateOperation


class ApiUsageService(CreateOperation):
    repo = ApiUsageRepository
    schema_out = None