# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

from typing import Dict, List, Optional, Union, Tuple

import aiohttp

from omni.services.browser.asset import BaseAssetStore, AssetModel, SearchCriteria, ProviderModel
from .constants import SETTING_STORE_ENABLE
from pathlib import Path
import logging

CURRENT_PATH = Path(__file__).parent
DATA_PATH = CURRENT_PATH.parent.parent.parent.parent.joinpath("data")

# The name of your company
PROVIDER_ID = "Laubwerk"
# The URL location of your API
STORE_URL = "https://api.laubwerk.com/1/search"


class LaubwerkAssetProvider(BaseAssetStore):
    """ Laubwerk asset provider implementation.
    """

    def __init__(self, ov_app="Kit", ov_version="na") -> None:
        super().__init__(PROVIDER_ID)
        self._ov_app = ov_app
        self._ov_version = ov_version

    async def _search(self, search_criteria: SearchCriteria) -> Tuple[List[AssetModel], bool]:
        """ Searches the asset store.

            This function needs to be implemented as part of an implementation of the BaseAssetStore.
            This function is called by the public `search` function that will wrap this function in a timeout.
        """
        params = {}

        assets: List[AssetModel] = []

        logger = logging.getLogger(__name__)
        logger.error("search() function called.")

        # Setting for filter search criteria
        if search_criteria.filter.categories:
            # No category search, also use keywords instead
            categories = search_criteria.filter.categories
            all_category_keywords = []
            for category in categories:
                if category.startswith("/"):
                    category = category[1:]
                category_keywords = category.split("/")
                #params["filter[categories]"] = ",".join(category_keywords).lower()
                all_category_keywords.extend(category_keywords)

            # If we are not in the vegetation category, we give up and just
            # return an empty result.
            if not "Vegetation" in all_category_keywords:
                return (assets, False)

            # Since we only operate in the Vegetation space, we remove that
            # category keyword, because it is meaningless for us.
            all_category_keywords.remove("Vegetation")

            # TODO: We currently don't have categories in our API, but we should
            # add that, soon. We should then map the sub-categories "Tree",
            # "Plants", "Grass", and "Bush" to our own categories and add the
            # result to the query.

        # Setting for keywords search criteria
        if search_criteria.keywords:
            params["query"] = "+".join(search_criteria.keywords)

        # Setting for page number search criteria
        if search_criteria.page.number:
            params["page"] = search_criteria.page.number

        # Setting for max number of items per page 
        if search_criteria.page.size:
            params["per_page"] = search_criteria.page.size

        #params["filter[.relationships.collections.data]"] = "includes(kit-freebie,id)"

        # Call the search resource with the assembled parameters and the guest
        # login.
        headers = {"Authorization": "Basic Z3Vlc3Q6bGF1Yndlcms="}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(f"{STORE_URL}", params=params) as resp:
                #result = await resp.read()
                result = await resp.json()

        logger.error(result)
        items = result["data"]

        assets: List[AssetModel] = []

        # Create AssetModels based off of JSON data
        for item in items:
            # Grab the thumbnail reference for this item
            thumbnail_type = None
            thumbnail_id = None
            thumbnail_url = ""
            try:
                thumbnail_id = item["relationships"]["header"]["data"]["id"]
                thumbnail_type = item["relationships"]["header"]["data"]["type"]
            except:
                pass
            else:
                # Find the thumbnail reference in the included image resources
                for resource in result["included"]:
                    if resource["id"] == thumbnail_id and resource["type"] == thumbnail_type:
                        thumbnail_url = resource["links"]["source"]
                        break
            
            # Try to retrieve the botanical name, use script name as fallback.
            item_name = item["attributes"]["name"]
            try:
                item_name = item["attributes"]["botanicalName"]
            except:
                pass

            # Add the entry to the asset list
            assets.append(
                AssetModel(
                    identifier=item["id"],
                    name=item_name,
                    published_at="2015-12-07T21:19:08+00:00",
                    categories=["Vegetation"],
                    tags=["broadleaf", "temperate"],
                    vendor=PROVIDER_ID,
                    product_url="https://stage.api.laubwerk.com/1/images/1086/file?size=thumbnail",
                    download_url="https://stage.api.laubwerk.com/1/images/1086/file?size=thumbnail",
                    price=0.0,
                    thumbnail=thumbnail_url,
                )
            )

        # Are there more assets that we can load?
        more = False if result["links"]["next"] == None else True

        return (assets, more)

    def provider(self) -> ProviderModel:
        """Return provider info"""
        return ProviderModel(
            name=PROVIDER_ID, icon=f"{DATA_PATH}/laubwerk-64x64.png", enable_setting=SETTING_STORE_ENABLE
        )
