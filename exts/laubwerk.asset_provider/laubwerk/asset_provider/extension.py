# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
import importlib

import carb
import carb.settings
import carb.tokens

import omni.ext

from omni.services.browser.asset import get_instance as get_asset_services
from .laubwerk import LaubwerkAssetProvider
from .constants import SETTING_STORE_ENABLE
import logging

class LaubwerkAssetProviderExtension(omni.ext.IExt):
    """ Laubwerk Asset Provider extension.
    """

    def on_startup(self, ext_id):
        self._asset_provider = LaubwerkAssetProvider()
        self._asset_service = get_asset_services()
        self._asset_service.register_store(self._asset_provider)
        carb.settings.get_settings().set(SETTING_STORE_ENABLE, True)
        
        logger = logging.getLogger(__name__)
        logger.error("on_startup() function called.")
       

    def on_shutdown(self):
        self._asset_service.unregister_store(self._asset_provider)
        carb.settings.get_settings().set(SETTING_STORE_ENABLE, False)
        self._asset_provider = None
        self._asset_service = None
