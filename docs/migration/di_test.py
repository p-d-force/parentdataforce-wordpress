import sys
try:
    from providers import get_provider_profile
    p = get_provider_profile("deepinfra")
    print("PROFILE:", p)
    if p:
        print("name:", p.name, "| aliases:", p.aliases)
        print("base_url:", p.base_url)
        print("env_vars:", p.env_vars)
        print("auth_type:", p.auth_type)
        print("fallback_models:", p.fallback_models)
        print("default_aux_model:", p.default_aux_model)
        print("has fetch_models:", hasattr(p, "fetch_models"))
        try:
            print("default_vision_model:", p.default_vision_model())
        except Exception as e:
            print("vision_model err:", repr(e))
except Exception as e:
    print("IMPORT ERROR:", repr(e))
