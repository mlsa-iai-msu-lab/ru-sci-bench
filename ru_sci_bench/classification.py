import json
from typing import Union

import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import GridSearchCV
from sklearn.neighbors import NearestNeighbors
from sklearn.svm import LinearSVC

from ru_sci_bench.utils import DataPaths, load_embeddings_from_jsonl, print_metrics

np.random.seed(1)


def get_ru_sci_bench_metrics(
    embeddings_path: str,
    metrics: Union[str, list[str]] = "all",
    get_cls_report: bool = False,
    grid_search_cv: bool = False,
    n_jobs: int = -1,
    max_iter: int = 100,
    silent: bool = False,
) -> dict:
    """Run ruSciBench tasks.

    Arguments:
        embeddings_path -- path to the jsonl with embeddings
        metrics -- metric or list of metrics to calculate (ru_, en_, full_ classification
            tasks or translation_search) or 'all'
        get_cls_report -- if True, will return classification_report in classification tasks
        grid_search_cv -- if True, will use cross-validation to choose regularization parameter C
            in the classification tasks
        n_jobs -- number of jobs to run in parallel in GridSearchCV (classification)
            or NearestNeighbors (translation_search)
        max_iter -- maximum number of iterations to fit LinearSVC model (classification)
        silent -- silent all outputs

    Returns:
        metrics -- dictionary with macro average F1, weighted average F1 and optionally classification_report
            for classification tasks and Recall@1 for translation_search task
    """
    data_paths = DataPaths()
    if not silent:
        print("Loading embeddings...")
    embeddings = load_embeddings_from_jsonl(embeddings_path)

    results = {}

    if metrics in ["all", "translation_search"] or "translation_search" in metrics:
        if not silent:
            print("Running the eLibrary translation search task...")
        ru_embs, en_embs = get_embeddings_for_translation_search(
            embeddings, data_paths.ru_en_translation_test
        )

        results["ru_en_translation_search"] = translation_search(
            queries_embs=ru_embs, results_embs=en_embs, n_jobs=n_jobs
        )
        print_metrics("ru_en_translation_search", results, silent)

        results["en_ru_translation_search"] = translation_search(
            queries_embs=en_embs, results_embs=ru_embs, n_jobs=n_jobs
        )
        print_metrics("en_ru_translation_search", results, silent)

    if metrics in ["all", "full_classification"] or "full_classification" in metrics:
        if not silent:
            print("Running the eLibrary OECD-full task...")
        X_train, X_test, y_train, y_test = get_X_y_for_classification(
            embeddings,
            data_paths.elibrary_oecd_full_train,
            data_paths.elibrary_oecd_full_test,
        )
        results["elibrary_oecd_full"] = classify(
            X_train,
            y_train,
            X_test,
            y_test,
            get_cls_report=get_cls_report,
            grid_search_cv=grid_search_cv,
            n_jobs=n_jobs,
            max_iter=max_iter,
            silent=silent,
        )
        print_metrics("elibrary_oecd_full", results, silent)

        if not silent:
            print("Running the eLibrary GRNTI-full task...")
        X_train, X_test, y_train, y_test = get_X_y_for_classification(
            embeddings,
            data_paths.elibrary_grnti_full_train,
            data_paths.elibrary_grnti_full_test,
        )
        results["elibrary_grnti_full"] = classify(
            X_train,
            y_train,
            X_test,
            y_test,
            get_cls_report=get_cls_report,
            grid_search_cv=grid_search_cv,
            n_jobs=n_jobs,
            max_iter=max_iter,
            silent=silent,
        )
        print_metrics("elibrary_grnti_full", results, silent)

    if metrics in ["all", "ru_classification"] or "ru_classification" in metrics:
        if not silent:
            print("Running the eLibrary OECD-ru task...")
        X_train, X_test, y_train, y_test = get_X_y_for_classification(
            embeddings,
            data_paths.elibrary_oecd_ru_train,
            data_paths.elibrary_oecd_ru_test,
        )
        if not silent:
            print("Classifier training...")
        results["elibrary_oecd_ru"] = classify(
            X_train,
            y_train,
            X_test,
            y_test,
            get_cls_report=get_cls_report,
            grid_search_cv=grid_search_cv,
            n_jobs=n_jobs,
            max_iter=max_iter,
            silent=silent,
        )
        print_metrics("elibrary_oecd_ru", results, silent)

        if not silent:
            print("Running the eLibrary GRNTI-ru task...")
        X_train, X_test, y_train, y_test = get_X_y_for_classification(
            embeddings,
            data_paths.elibrary_grnti_ru_train,
            data_paths.elibrary_grnti_ru_test,
        )
        if not silent:
            print("Classifier training...")
        results["elibrary_grnti_ru"] = classify(
            X_train,
            y_train,
            X_test,
            y_test,
            get_cls_report=get_cls_report,
            grid_search_cv=grid_search_cv,
            n_jobs=n_jobs,
            max_iter=max_iter,
            silent=silent,
        )
        print_metrics("elibrary_grnti_ru", results, silent)

    if metrics in ["all", "en_classification"] or "en_classification" in metrics:
        if not silent:
            print("Running the eLibrary OECD-en task...")
        X_train, X_test, y_train, y_test = get_X_y_for_classification(
            embeddings,
            data_paths.elibrary_oecd_en_train,
            data_paths.elibrary_oecd_en_test,
        )
        if not silent:
            print("Classifier training...")
        results["elibrary_oecd_en"] = classify(
            X_train,
            y_train,
            X_test,
            y_test,
            get_cls_report=get_cls_report,
            grid_search_cv=grid_search_cv,
            n_jobs=n_jobs,
            max_iter=max_iter,
            silent=silent,
        )
        print_metrics("elibrary_oecd_en", results, silent)

        if not silent:
            print("Running the eLibrary GRNTI-en task...")
        X_train, X_test, y_train, y_test = get_X_y_for_classification(
            embeddings,
            data_paths.elibrary_grnti_en_train,
            data_paths.elibrary_grnti_en_test,
        )
        if not silent:
            print("Classifier training...")
        results["elibrary_grnti_en"] = classify(
            X_train,
            y_train,
            X_test,
            y_test,
            get_cls_report=get_cls_report,
            grid_search_cv=grid_search_cv,
            n_jobs=n_jobs,
            max_iter=max_iter,
            silent=silent,
        )
        print_metrics("elibrary_grnti_en", results, silent)

    return results


def classify(
    X_train: np.array,
    y_train: np.array,
    X_test: np.array,
    y_test: np.array,
    grid_search_cv: bool = False,
    n_jobs: int = -1,
    max_iter: int = 100,
    get_cls_report: bool = False,
    silent: bool = False,
) -> dict:
    """
    Simple classification method using sklearn framework. LinearSVC model fits with default parameters.
        Optionally regularization parameter C can be chosen via cross-validation on X_train, y_train.

    Arguments:
        X_train, y_train -- training data
        X_test, y_test -- test data to evaluate on
        grid_search_cv -- if True, will use cross-validation to choose regularization parameter
            C in classification tasks
        n_jobs -- number of jobs to run in parallel in GridSearchCV
        max_iter -- maximum number of iterations to fit LinearSVC model
        get_cls_report -- return classification_report

    Returns:
        metrics -- dict with macro average F1, weighted average F1 and optionally classification_report
            on X_test, y_test
    """
    estimator = LinearSVC(loss="squared_hinge", max_iter=max_iter, random_state=42)
    if grid_search_cv:
        svm = GridSearchCV(
            estimator=estimator,
            cv=3,
            param_grid={"C": np.logspace(-4, 2, 7)},
            verbose=not silent,
            n_jobs=n_jobs,
        )
    else:
        svm = estimator
    svm.fit(X_train, y_train)
    y_pred = svm.predict(X_test)
    result = {
        "macro_f1": f1_score(y_test, y_pred, average="macro"),
        "weighted_f1": f1_score(y_test, y_pred, average="weighted"),
    }
    if get_cls_report:
        result["cls_report"] = classification_report(y_test, y_pred)
    return result


def get_X_y_for_classification(
    embeddings: dict, train_path: str, test_path: str
) -> tuple[np.array, np.array, np.array, np.array]:
    """
    Preparing data for classification task

    Arguments:
        embeddings: embeddings dict
        train_path: path to the csv with train ids/labels
        test_path: path to the csv with test ids/labels

    Returns:
        X_train, X_test, y_train, y_test: train/test embeddings and labels
    """
    train = pd.read_csv(train_path)
    test = pd.read_csv(test_path)
    X_train = train.id.apply(lambda id_: embeddings[id_]).to_list()
    X_test = test.id.apply(lambda id_: embeddings[id_]).to_list()
    return np.array(X_train), np.array(X_test), train.label.to_numpy(), test.label.to_numpy()


def get_embeddings_for_translation_search(
    embeddings: dict, translation_test_path: str
) -> tuple[np.array, np.array]:
    """
    Preparing data for translation_search task

    Arguments:
        embeddings: embeddings dict
        translation_test_path: path to the russian-english translations file

    Returns:
        ru_embs, en_embs: embeddings for texts in russian and english
    """
    with open(translation_test_path) as f:
        translation_test = json.load(f)
    ru_embs = np.array([embeddings[int(id_)] for id_ in translation_test.keys()])
    en_embs = np.array([embeddings[int(id_)] for id_ in translation_test.values()])
    return ru_embs, en_embs


def translation_search(
    queries_embs: np.array, results_embs: np.array, n_jobs: int = -1
) -> dict[str, float]:
    """
    Method for checking whether the closest embedding in the dataset to the embedding
        of a text is of its translation. Returns a proportion of texts in the dataset for
        which it is true.

    Arguments:
        queries_embs -- embeddings to use as queries
        results_embs -- embeddings to use for searching
        n_jobs -- number of jobs to run in parallel in NearestNeighbors

    Returns:
        Dictionary with recall@1 metric
    """
    nearest_neighbor = NearestNeighbors(n_neighbors=1, metric="cosine", n_jobs=n_jobs)
    nearest_neighbor.fit(results_embs)
    _, top_index = nearest_neighbor.kneighbors(queries_embs)
    correct_indexes = np.arange(results_embs.shape[0])
    is_correct = (top_index.flatten() == correct_indexes).nonzero()[0]
    return {"recall@1": is_correct.shape[0] / len(correct_indexes)}
