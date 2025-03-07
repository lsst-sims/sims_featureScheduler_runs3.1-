import numpy as np
import pandas as pd
import matplotlib.pylab as plt
from rubin_sim.selfcal import generate_catalog, OffsetSys, OffsetSNR, LsqrSolver
import sqlite3
from rubin_sim.data import get_baseline


if __name__ == "__main__":

    filter_name = "r"

    old = False

    # Load up pointings
    if old:
        survey = '/Users/yoachim/git_repos/23_Scratch/sched_over_time/opsim3_61_sqlite.db'
    else:
        # survey = get_baseline()
        survey = '../selfcal_footprints/no_plane_v3.1_10yrs.db'
    con = sqlite3.connect(survey)

    if old:
        visits_df = pd.read_sql("select obsHistID as observationId, fieldra as ra,fielddec as "
                                "dec,fiveSigma as fiveSigmaDepth,rotSkyPos from Summary where filter='%s' and night < 360;" % filter_name, con)
    else:
        visits_df = pd.read_sql("select observationId, fieldra as ra,fielddec as "
                                "dec,fiveSigmaDepth,rotSkyPos from observations where filter='%s' and night < 360;" % filter_name, con)

    con.close()
    # what is the right way to do this? 
    names = ['observationId', 'ra', 'dec', 'fiveSigmaDepth', 'rotSkyPos']
    types = [int, float, float, float, float]
    visits = np.empty(visits_df.shape[0], dtype=list(zip(names, types)))
    for key in names:
        visits[key] = visits_df[key].values

    # If we are reading old database with radians
    if old:
        visits['ra'] = np.degrees(visits['ra'])
        visits['dec'] = np.degrees(visits['dec'])
        visits['rotSkyPos'] = np.degrees(visits['rotSkyPos'])

    # Load up stars
    con = sqlite3.connect("msrgb_1e6.sqlite")
    stars_df = pd.read_sql("select id,ra,decl,%smag from stars;" % filter_name, con)
    con.close()
    # what is the right way to do this? There's gotta be a better way!
    names = ['id', 'ra', 'decl', '%smag' % filter_name]
    types = [int, float, float, float]
    stars = np.empty(stars_df.shape[0], dtype=list(zip(names, types)))
    for key in names:
        stars[key] = stars_df[key].values

    # Set offsets to apply. Doing a 3% systematic to make sure there is some good noise
    offsets = [OffsetSys(error_sys=0.03), OffsetSNR(lsst_filter=filter_name)]
    observed_stars = generate_catalog(visits, stars, offsets=offsets, lsst_filter=filter_name)

    # Save results
    np.savez('test_generate.npz', observed_stars=observed_stars)

    # now to try running the solution
    solver = LsqrSolver(iter_lim=10000)
    solver.run()
