#-*- coding=utf-8 -*-
"""
Z
"""
import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer, Human
from sc2.constants import *
import random


class JimAI(sc2.BotAI):
    def __init__(self):
        self.ITERATIONS_PER_MINUTE = 165
        self.MAX_WORKERS = 60  # 限制最大农民数    

    async def on_step(self, iteration: int):
        """
        on_step这个异步方法必须被重写，再此将会调用你设置的每一步指令。
        """
        self.iteration = iteration
        await self.distribute_workers()
        await self.hatch_workers()
        await self.hatch_overloads()
        await self.build_extractors()
        await self.expand()
        await self.hatch_zergtech()
        await self.hatch_queen()
        await self.spawning_brooding()
        await self.attack()


    async def hatch_workers(self):
        '''
        20保证没矿drones不多造， 因为一下虫卵会一下造3个， 所以数量20刚刚好
        '''
        if len(self.units(HATCHERY)) * 20 > len(self.units(DRONE)):  # 每矿农民补满就不补了
            if len(self.units(DRONE)) < self.MAX_WORKERS:
                for larva in self.units(LARVA).ready.noqueue:
                    if self.can_afford(DRONE):
                        await self.do(larva.train(DRONE))    
                        
    async def hatch_overloads(self):
        if self.supply_left < 7 and not self.already_pending(OVERLORD):
            for larva in self.units(LARVA).ready.noqueue:
                if self.can_afford(OVERLORD):
                    await self.do(larva.train(OVERLORD))   
                    
    async def build_extractors(self):
        """
        建造气矿
        """
        for hat in self.units(HATCHERY).ready:
            vespenes = self.state.vespene_geyser.closer_than(15.0, hat)
            for vespene in vespenes:
                if not self.can_afford(EXTRACTOR):
                    break
                worker = self.select_build_worker(vespene.position)
                if worker is None:
                    break
                if not self.units(EXTRACTOR).closer_than(1.0, vespene).exists:
                    await self.do(worker.build(EXTRACTOR, vespene))    
                    
    async def expand(self):
        """
        何时扩张 简化版
        基地数量少于3个就立即扩张
        """
        if self.units(HATCHERY).amount < 2 and self.can_afford(HATCHERY) and not self.already_pending(HATCHERY):
            await self.expand_now()     
            
    async def hatch_zergtech(self):
        hat = self.units(HATCHERY).ready
        if not self.units(SPAWNINGPOOL).ready.exists:
            if hat.exists:
                if self.can_afford(SPAWNINGPOOL) and not self.already_pending(SPAWNINGPOOL):
                    await self.build(SPAWNINGPOOL, near=hat.first)
        elif not self.units(ROACHWARREN).ready.exists:
            if self.can_afford(ROACHWARREN) and not self.already_pending(ROACHWARREN):
                if hat.exists:
                    await self.build(ROACHWARREN, near=hat.first)
            
             
    async def hatch_queen(self):
        if self.units(SPAWNINGPOOL).ready.exists:
            if len(self.units(HATCHERY)) > len(self.units(QUEEN)):
                for hat in self.units(HATCHERY).ready.noqueue:
                    if self.can_afford(QUEEN):
                        await self.do(hat.train(QUEEN))
                        
                        
    async def spawning_brooding(self):
        for larva in self.units(LARVA).ready.noqueue:
            if self.units(ROACHWARREN).ready.exists:
                await self.do(larva.train(ROACH))

    def find_target(self, state):
        """
        寻找敌方单位
        注意这个函数不是异步的，不用加async
        """
        if len(self.known_enemy_units) > 0:
            return random.choice(self.known_enemy_units)
        elif len(self.known_enemy_structures) > 0:
            return random.choice(self.known_enemy_structures)
        else:
            return self.enemy_start_locations[0]
        
    async def attack(self):
        #attack
        if self.units(ROACH).amount > 20:
            for r in self.units(ROACH).idle:
                await self.do(r.attack(self.find_target(self.state)))

        #defend
        if self.units(ROACH).amount > 8:
            if len(self.known_enemy_units) > 0:
                for r in self.units(ROACH).idle:
                    await self.do(r.attack(random.choice(self.known_enemy_units)))


def main():
    run_game(maps.get("AutomatonLE"), [
        #Human(Race.Terran),
        Bot(Race.Zerg, JimAI()),
        Computer(Race.Protoss, Difficulty.Hard)
        ], realtime=False) 


if __name__ == '__main__':
    main()