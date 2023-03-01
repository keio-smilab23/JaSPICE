"""
Callback server
"""
import uvicorn
import numpy as np
from tqdm import tqdm

from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from typing import List, Dict
from jaspice.metrics import BatchJaSPICE


class ReqItem(BaseModel):
    references: List[List[str]]
    candidates: List[str]
    batch_size: int = 16


class CallbackServer:
    @staticmethod
    def start():
        """
        Function of start http server
        """
        fapi = FastAPI()

        @fapi.post("/coco")
        def coco(references: Dict[str, List[str]], candidates: Dict[str, List[str]]):
            pass

        @fapi.post("/")
        def compute_jaspice(item: ReqItem):
            jaspice = BatchJaSPICE(size=item.batch_size)
            spice, N = [], len(item.candidates)
            batch_cand, batch_refs = [], []
            for i, (reference, candidate) in enumerate(tqdm(zip(item.references, item.candidates))):
                batch_refs.append(reference)
                batch_cand.append(candidate)
                if (i + 1) % item.batch_size == 0 or i == N - 1:
                    results = jaspice(
                        batch_candidate=batch_cand,
                        batch_references=batch_refs)
                    spice.extend(results)
                    batch_cand, batch_refs = [], []

            return JSONResponse(content=spice)

        host_name = "0.0.0.0"
        port_num = 2115
        uvicorn.run(fapi, host=host_name, port=port_num)


def main():
    server = CallbackServer()
    server.start()


if __name__ == "__main__":
    main()
