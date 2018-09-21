# coding: utf-8
# *First compiled on May 5, 2017. Updated August 14, 2018.*
# # Clustering 3k PBMCs following a Seurat Tutorial
#
# This started out with a demonstration that Scanpy would allow to reproduce most of Seurat's ([Satija *et al.*, 2015](https://doi.org/10.1038/nbt.3192)) clustering tutorial as described on http://satijalab.org/seurat/pbmc3k_tutorial.html (July 26, 2017), which we gratefully acknowledge. In the meanwhile, we have added and removed several pieces.
#
# The data consists in *3k PBMCs from a Healthy Donor* and is freely available from 10x Genomics ([here](http://cf.10xgenomics.com/samples/cell-exp/1.1.0/pbmc3k/pbmc3k_filtered_gene_bc_matrices.tar.gz) from this [webpage](https://support.10xgenomics.com/single-cell-gene-expression/datasets/1.1.0/pbmc3k)).


import matplotlib as mpl
mpl.use('agg')
from matplotlib.testing.compare import compare_images
import matplotlib.pyplot as pl
import numpy as np
import os
import scanpy.api as sc

ROOT = os.path.dirname(os.path.abspath(__file__)) + '/pbmc3k_images/'

tolerance = 13  # default matplotlib pixel difference tolerance

def save_and_compare_images(basename):
    if not os.path.exists('./figures/'): os.makedirs('./figures/')
    outname = './figures/' + basename + '.png'
    pl.savefig(outname, dpi=80)
    pl.close()
    res = compare_images(ROOT + '/' + basename + '.png', outname, tolerance)
    assert res is None, res

def test_pbmc3k():

    adata = sc.read('./data/pbmc3k_raw.h5ad', backup_url='http://falexwolf.de/data/pbmc3k_raw.h5ad')

    # Preprocessing

    sc.pl.highest_expr_genes(adata, n_top=20)
    save_and_compare_images('highest_expr_genes')

    sc.pp.filter_cells(adata, min_genes=200)
    sc.pp.filter_genes(adata, min_cells=3)

    mito_genes = [name for name in adata.var_names if name.startswith('MT-')]
    # for each cell compute fraction of counts in mito genes vs. all genes
    # the `.A1` is only necessary as X is sparse to transform to a dense array after summing
    adata.obs['percent_mito'] = np.sum(
        adata[:, mito_genes].X, axis=1).A1 / np.sum(adata.X, axis=1).A1
    # add the total counts per cell as observations-annotation to adata
    adata.obs['n_counts'] = adata.X.sum(axis=1).A1

    sc.pl.violin(adata, ['n_genes', 'n_counts', 'percent_mito'],
                 jitter=False, multi_panel=True)
    save_and_compare_images('violin')

    sc.pl.scatter(adata, x='n_counts', y='percent_mito')
    save_and_compare_images('scatter_1')
    sc.pl.scatter(adata, x='n_counts', y='n_genes')
    save_and_compare_images('scatter_2')

    adata = adata[adata.obs['n_genes'] < 2500, :]
    adata = adata[adata.obs['percent_mito'] < 0.05, :]

    adata.raw = sc.pp.log1p(adata, copy=True)

    sc.pp.normalize_per_cell(adata, counts_per_cell_after=1e4)

    filter_result = sc.pp.filter_genes_dispersion(
        adata.X, min_mean=0.0125, max_mean=3, min_disp=0.5)
    sc.pl.filter_genes_dispersion(filter_result)
    save_and_compare_images('filter_genes_dispersion')

    adata = adata[:, filter_result.gene_subset]
    sc.pp.log1p(adata)
    sc.pp.regress_out(adata, ['n_counts', 'percent_mito'])
    sc.pp.scale(adata, max_value=10)

    # PCA

    sc.tl.pca(adata, svd_solver='arpack')
    sc.pl.pca(adata, color='CST3')
    save_and_compare_images('pca')

    sc.pl.pca_variance_ratio(adata, log=True)
    save_and_compare_images('pca_variance_ratio')

    # UMAP

    sc.pp.neighbors(adata, n_neighbors=10, n_pcs=40)
    # sc.tl.umap(adata)  # umaps lead to slight variations

    # sc.pl.umap(adata, color=['CST3', 'NKG7', 'PPBP'], use_raw=False)
    # save_and_compare_images('umap_1')

    # Clustering the graph

    sc.tl.louvain(adata)
    # sc.pl.umap(adata, color=['louvain', 'CST3', 'NKG7'])
    # save_and_compare_images('umap_2')
    sc.pl.scatter(adata, 'CST3', 'NKG7', color='louvain')
    save_and_compare_images('scatter_3')

    # Finding marker genes

    sc.tl.rank_genes_groups(adata, 'louvain')
    sc.pl.rank_genes_groups(adata, n_genes=20, sharey=False)
    save_and_compare_images('rank_genes_groups_1')

    sc.tl.rank_genes_groups(adata, 'louvain', method='logreg')
    sc.pl.rank_genes_groups(adata, n_genes=20, sharey=False)
    save_and_compare_images('rank_genes_groups_2')

    sc.tl.rank_genes_groups(adata, 'louvain', groups=['0'], reference='1')
    sc.pl.rank_genes_groups(adata, groups='0', n_genes=20)
    save_and_compare_images('rank_genes_groups_3')

    # gives a strange error, probably due to jitter or something
    # sc.pl.rank_genes_groups_violin(adata, groups='0', n_genes=8)
    # save_and_compare_images('rank_genes_groups_4')

    new_cluster_names = [
        'CD4 T cells', 'CD14+ Monocytes',
        'B cells', 'CD8 T cells',
        'NK cells', 'FCGR3A+ Monocytes',
        'Dendritic cells', 'Megakaryocytes']
    adata.rename_categories('louvain', new_cluster_names)

    # sc.pl.umap(adata, color='louvain', legend_loc='on data', title='', frameon=False)
    # save_and_compare_images('umap_3')
    
    sc.pl.violin(adata, ['CST3', 'NKG7', 'PPBP'], groupby='louvain', rotation=90)
    save_and_compare_images('violin_2')