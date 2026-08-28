// Quantum Particle Swarm Optimization (QPSO) for Traffic Light Timing
// Decision Variables: NS_GREEN duration for each intersection
// Objective: Minimize a fitness function based on current queues and wait times

export class QPSOOptimizer {
  constructor(numIntersections, swarmSize = 20, maxIterations = 50) {
    this.D = numIntersections;
    this.swarmSize = swarmSize;
    this.maxIterations = maxIterations;
    
    // Bounds for NS_GREEN time (seconds)
    this.minBound = 10;
    this.maxBound = 40;

    this.swarm = [];
    this.globalBestPos = new Array(this.D).fill(0);
    this.globalBestFitness = Infinity;

    this.convergenceHistory = [];
    
    this.initSwarm();
  }

  initSwarm() {
    this.swarm = [];
    for (let i = 0; i < this.swarmSize; i++) {
      let pos = [];
      for (let d = 0; d < this.D; d++) {
        pos[d] = this.minBound + Math.random() * (this.maxBound - this.minBound);
      }
      this.swarm.push({
        pos: [...pos],
        pbestPos: [...pos],
        pbestFitness: Infinity
      });
    }
  }

  // Fitness function: Evaluate proposed timings against current queue states
  evaluateFitness(pos, intersectionStates, ambulanceState = null) {
    let penalty = 0;

    for (let d = 0; d < this.D; d++) {
      const state = intersectionStates[d];
      if (!state) continue;

      const proposedNS = pos[d];

      // Proxy objective: 
      // Higher queues mean we need longer cycles or specific timings
      let idealNS = 20; // Default base line
      if (state.queueCount > 5) idealNS = 30;
      else if (state.queueCount > 2) idealNS = 25;

      penalty += Math.pow(proposedNS - idealNS, 2);

      // PHASE 5: Ambulance Constraint Handling
      if (ambulanceState && ambulanceState.targetIntersectionId === state.id) {
        // If ambulance needs NS green and proposed is low, huge penalty
        if (ambulanceState.direction === "NS" && proposedNS < 35) {
          penalty += 10000; 
        } else if (ambulanceState.direction === "EW" && proposedNS > 15) {
          penalty += 10000;
        }
      }
    }
    return penalty;
  }

  optimize(intersectionStates, ambulanceState = null) {
    this.initSwarm();
    this.globalBestFitness = Infinity;
    this.convergenceHistory = [];

    for (let iter = 0; iter < this.maxIterations; iter++) {
      // 1. Calculate mbest (Mean Best Position)
      let mbest = new Array(this.D).fill(0);
      for (let i = 0; i < this.swarmSize; i++) {
        for (let d = 0; d < this.D; d++) {
          mbest[d] += this.swarm[i].pbestPos[d];
        }
      }
      for (let d = 0; d < this.D; d++) {
        mbest[d] /= this.swarmSize;
      }

      // 2. Contraction-Expansion Coefficient (alpha)
      // Linearly decreasing from 1.0 to 0.5
      const alpha = 1.0 - 0.5 * (iter / this.maxIterations);

      for (let i = 0; i < this.swarmSize; i++) {
        let particle = this.swarm[i];
        
        // Evaluate fitness
        const fitness = this.evaluateFitness(particle.pos, intersectionStates, ambulanceState);

        // Update pbest
        if (fitness < particle.pbestFitness) {
          particle.pbestFitness = fitness;
          particle.pbestPos = [...particle.pos];
        }

        // Update gbest
        if (fitness < this.globalBestFitness) {
          this.globalBestFitness = fitness;
          this.globalBestPos = [...particle.pos];
        }

        // Update particle position (QPSO Equation)
        for (let d = 0; d < this.D; d++) {
          const phi = Math.random();
          // local attractor
          const p = (phi * particle.pbestPos[d] + (1 - phi) * this.globalBestPos[d]);
          const u = Math.random();
          const L = alpha * Math.abs(mbest[d] - particle.pos[d]);
          
          if (Math.random() > 0.5) {
            particle.pos[d] = p + L * Math.log(1 / u);
          } else {
            particle.pos[d] = p - L * Math.log(1 / u);
          }

          // Boundary enforcement
          if (particle.pos[d] < this.minBound) particle.pos[d] = this.minBound;
          if (particle.pos[d] > this.maxBound) particle.pos[d] = this.maxBound;
        }
      }
      
      this.convergenceHistory.push(this.globalBestFitness);
    }

    return {
      bestTimings: this.globalBestPos, // Array of NS_GREEN durations
      convergence: this.convergenceHistory
    };
  }
}
