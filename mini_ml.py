"""
Mini_ML - [Mini]malistic [M]achine-[L]earning Toolset.
Designed for quick model exploration, training and usage.
"""

# Import statements.
import os
import joblib
from pandas import DataFrame
from numpy import ndarray, arange
from scipy.stats import randint, uniform


class MiniML:
    """
    Minimalistic toolset for machine-learning training and prediction.
    Why: Used for quick development, testing and usage of models.
    """

    def __init__(self):
        pass

    """ Usage Methods"""

    def train(self, training_dataset: DataFrame, input_column_names: list,
              target_column_name: str, train_test_ratio: float) -> None:
        """
        If model already exists continue training (or retrain if continuation not possible) and if model doesn't exist,
        train from scratch with multi-stage training setup from Data1: i.e. train various models based on dataset,
        select top 3 and optimise their hyperparameters for better performance. Model is saved to file, not returned.
        Why: Train, improve or retrain models with one function for simplicity.

        Note: The model is always saved to ./models/model_{target_column_name}.pkl

        Parameters
        ----------
        training_dataset : Input data to train the model on.
        input_column_names : Names of columns we want to use as input to predict values with.
        target_column_name : Name of column we want to train our model to predict the values of.
        train_test_ratio : The ratio of Training + Validation to Testing data.

        Returns
        -------
        None : This function saves the trained model to file, so no return is necessary.

        Sample Usage
        ------------
        import meow                                                  # Ensure class is imported.
        from pandas import read_csv                                  # (External package to read data from CSV.)
        ml = meow.ML()                                               # Create instance of class.
        training_dataset = read_csv("training_dataset.csv")          # Load dataset for training.
        input_column_names = ["phi_d", "df_d", "j_d", "j"]           # What features (columns) you want to predict with.
        target_column_name = "eta_is"                                # What component you want predicted.
        train_test_ratio = 0.8                                       # What data % to dedicate to training (vs testing).
        ml.train(training_dataset, input_column_names, target_column_name, train_test_ratio)  # Train model.
        """

        try:
            # Find and continue training model (or retrain, if necessary).
            _ = self._find_and_load_model(target_column_name)
            self._continue_training_model(training_dataset, input_column_names, target_column_name, train_test_ratio)

        except FileNotFoundError:
            # If model not found, train from scratch with multi-stage model training from Data1.
            self._train_models_in_stages(training_dataset, input_column_names, target_column_name, train_test_ratio)

    def predict(self, input_dataset: DataFrame, target_column_name: str) -> ndarray:
        """
        Predict target value(s) based on input dataset provided, with automated model identification.
        Why: Allows for quick prediction of values without the hassle of specifying a model and its path.

        Note: This function checks the folder and all directories within the folder its located in for
        the relevant model. If the model is not located within the above-mentioned path, this function will error.

        Parameters
        ----------
        input_dataset : Input data to use as model input.
        target_column_name : Name of target of prediction. (e.g. eta_is, phi_op, etc.)

        Returns
        -------
        prediction_set : A set of model predictions for provided inputs.

        Sample Usage
        ------------
        import meow                                                     # Ensure class is imported.
        from pandas import read_csv                                     # (External package to read data from CSV.)
        ml = meow.ML()                                                  # Create instance of class.
        input_dataset = read_csv("input_dataset.csv")                   # Load dataset for prediction.
        target_column_name = "eta_is"                                   # What component you want predicted.
        prediction_set = ml.predict(input_dataset, target_column_name)  # Obtain ML prediction, if model exists.
        """

        # Find and load the relevant model based on prediction target.
        model = self._find_and_load_model(target_column_name)

        # Ensure dataset only has features (columns) expected by the model.
        expected_features = model.feature_names_in_
        input_dataset_filtered = input_dataset[expected_features]

        # Predict using the filtered input dataset.
        prediction_set = model.predict(input_dataset_filtered)

        return prediction_set

    """ Support Methods """

    def _train_models_in_stages(self, dataset: DataFrame, input_column_names: list, target_column_name: str,
                                ratio: float) -> None:
        """
        Train various models based on dataset, select top 3 and optimise their hyperparameters for better performance.
        Why: Find the most performant model, and its most performant hyperparameter set, for a given dataset.

        Parameters
        ----------
        dataset : Input data to train the model on.
        input_column_names : Names of columns we want to use as input to predict values with.
        target_column_name : Name of column we want to train our model to predict the values of.
        ratio : The ratio of Training + Validation to Testing data.

        Returns
        -------
        None : This function saves the trained model to file, so no return is necessary.
        """

        # Down-select the dataset to only relevant columns.
        relevant_columns = input_column_names + [target_column_name]
        dataset = dataset[relevant_columns]

        # Perform stage 1 of training via a general model search.
        top_three_models = self._stage_1_model_training(dataset, target_column_name, ratio)

        # Perform stage 2 of training via hyperparameter optimisation of 3 most performant models found in stage 1.
        best_model = self._stage_2_model_training(top_three_models, dataset, target_column_name, ratio)

        # Save the best performing model to file.
        model_directory = './models'
        model_save_path = f'{model_directory}/model_{target_column_name}.pkl'
        os.makedirs(model_directory, exist_ok=True)
        joblib.dump(best_model, model_save_path)
        print(f"\nModel {target_column_name} two-stage training complete."
              f"\nBest model ({type(best_model).__name__}) saved to {model_save_path}\n")

    def _stage_1_model_training(self, input_dataset: DataFrame, target_column_name: str, ratio: float):
        """
        Train multiple models, evaluate their performance and return top performing three,
        Why: To find out which models perform the best prior to spending large compute on hyperparameter optimisation.

        Parameters
        ----------
        input_dataset : Input data to train the model on.
        target_column_name : Name of column we want to train our model to predict the values of.
        ratio : The ratio of Training + Validation to Testing data.

        Returns
        -------
        top_three_models : The three models with the lowest MSE score when evaluated against unseen test dataset.
        """

        # Load relevant libraries, if not already cached.
        r2_score = self._import_and_cache('r2_score')
        grid_search_cv = self._import_and_cache('GridSearchCV')
        train_test_split = self._import_and_cache('train_test_split')
        mean_squared_error = self._import_and_cache('mean_squared_error')

        # Load model types and some of their hyperparameters for initial processing.
        shallow_param_grids, _ = self._load_parameter_grids()

        # Split dataset into feature and target DataFrames for train model training.
        features = input_dataset.drop(columns=target_column_name)
        targets = input_dataset[target_column_name]

        # Convert targets to a 1D array to avoid scikit-learn warning spam.
        targets = targets.values.ravel()

        # Split data into training and testing sets to have data
        # that has never before been seen act as final evaluation of the model.
        x_train, x_test, y_train, y_test = train_test_split(
            features,
            targets,
            test_size=1 - ratio,
            random_state=42)

        # Train and evaluate each model with minor hyperparameter tuning to get an idea of what models work well
        # for this particular dataset / problem.
        results = {}
        best_models = {}
        for model_name, param_grid in shallow_param_grids.items():
            match model_name:
                case 'Support Vector Machine':
                    support_vector_machine = self._import_and_cache('SVR')
                    model = support_vector_machine()
                case 'Linear Regression':
                    linear_regression = self._import_and_cache('LinearRegression')
                    model = linear_regression()
                    # Skip GridSearchCV for Linear Regression as there are
                    # no hyperparameters to tune for this LR.
                    model.fit(x_train, y_train)
                case 'K-Nearest Neighbors':
                    k_neighbors_regressor = self._import_and_cache('KNeighborsRegressor')
                    model = k_neighbors_regressor()
                case 'Decision Tree':
                    decision_tree_regressor = self._import_and_cache('DecisionTreeRegressor')
                    model = decision_tree_regressor(random_state=42)
                case 'RandomForest':
                    random_forest_regressor = self._import_and_cache('RandomForestRegressor')
                    model = random_forest_regressor(random_state=42)
                case _:
                    model = None

            if model_name != 'Linear Regression':
                # Train model with cross-validation, varying hyperparameters via grid search.
                grid_search = grid_search_cv(model, param_grid, cv=5, scoring='neg_mean_squared_error')
                grid_search.fit(x_train, y_train)

                # Get the best model version from grid search.
                best_model_version = grid_search.best_estimator_
            else:
                # If Linear Regression, the best model version is the fitted model itself.
                best_model_version = model
            best_models[model_name] = best_model_version

            # Evaluate model against previously unseen data.
            test_predictions = best_model_version.predict(x_test)
            test_mse = mean_squared_error(y_test, test_predictions)
            test_r2 = r2_score(y_test, test_predictions)
            results[model_name] = {'Test MSE': test_mse, 'Test R²': test_r2}

        # Display results sorted by Test MSE.
        print(f"\n\n: : : {target_column_name} : : : \n\nStage 1 - General model search:\n")
        sorted_model_performances = sorted(results.items(), key=lambda x: x[1]['Test MSE'])
        for model_name, metrics in sorted_model_performances:
            print(f'Test MSE = {metrics["Test MSE"]:.4f}, Test R² = {metrics["Test R²"]:.4f} - {model_name}')

        # Select the top 3 performing models.
        top_three_models = [(model_name, best_models[model_name]) for model_name, _ in sorted_model_performances[:3]]

        return top_three_models

    def _stage_2_model_training(self, top_three_models, input_dataset: DataFrame, target_column_name: str,
                                ratio: float):
        """
        Optimise hyperparameters of top three models.
        Why: To find out which models perform the best prior to spending large compute on hyperparameter optimisation.

        Parameters
        ----------
        top_three_models : Top three models with the lowest Test MSE score from Training Stage 1.
        input_dataset : Input data to train the model on.
        target_column_name : Name of column we want to train our model to predict the values of.
        ratio : The ratio of Training + Validation to Testing data.

        Returns
        -------
        top_model : Model with the lowest Test MSE score after completing training with hyperparameter optimisation.
        """

        # Load relevant libraries, if not already cached.
        r2_score = self._import_and_cache('r2_score')
        train_test_split = self._import_and_cache('train_test_split')
        mean_squared_error = self._import_and_cache('mean_squared_error')
        randomised_search_cv = self._import_and_cache('RandomizedSearchCV')

        # Load model types and some of their hyperparameters for initial processing.
        _, comprehensive_param_grid = self._load_parameter_grids()

        # Split dataset into feature and target DataFrames for train model training.
        features = input_dataset.drop(columns=target_column_name)
        targets = input_dataset[target_column_name]

        # Convert targets to a 1D array to avoid scikit-learn warning spam.
        targets = targets.values.ravel()

        # Split data into training and testing sets to have data
        # that has never before been seen act as final evaluation of the model.
        x_train, x_test, y_train, y_test = train_test_split(
            features,
            targets,
            test_size=1 - ratio,
            random_state=42)

        # Optimize hyperparameters of the top 3 models using RandomizedSearchCV.
        print("\nStage 2 - Hyperparameter optimization of top models:\n")

        # Optimise each of the three models.
        best_model, best_score = None, float('inf')
        for model_name, model_instance in top_three_models:
            if model_name in comprehensive_param_grid:
                model = model_instance
                param_dist = comprehensive_param_grid[model_name]
                random_search = randomised_search_cv(
                    model,
                    param_distributions=param_dist,
                    n_iter=150,
                    cv=5,
                    scoring='neg_mean_squared_error',
                    n_jobs=-1,
                    random_state=42,
                    verbose=0
                )
                random_search.fit(x_train, y_train)

                # Get the best model version from random search.
                best_model_version = random_search.best_estimator_

                # Evaluate model against previously unseen data.
                test_predictions = best_model_version.predict(x_test)
                test_mse = mean_squared_error(y_test, test_predictions)
                test_r2 = r2_score(y_test, test_predictions)

                print(f'Optimised: Test MSE = {test_mse:.4f}, '
                      f'Test R² = {test_r2:.4f}'
                      f' - {model_name}')

                # Save the best performing model based on MSE.
                if test_mse < best_score:
                    best_score = test_mse
                    best_model = best_model_version

        return best_model

    def _continue_training_model(self, input_dataset: DataFrame, input_column_names: list, target_column_name: str,
                                 train_test_ratio: float) -> None:
        """
        Continue training a particular model (if possible), with automated model identification.
        Why: To avoid losing progress from prior training runs where possible such that less total compute is used.

        Parameters
        ----------
        input_dataset : Data to use as model input.
        input_column_names : Names of columns we want to use as input to predict values with.
        target_column_name : Name of column we want to train our model to predict the values of.
        train_test_ratio : The ratio of Training + Validation to Testing data.

        Returns
        -------
        None : This function saves the trained model to file, so not return is necessary.
        """

        # Load relevant libraries, if not already cached.
        r2_score = self._import_and_cache('r2_score')
        train_test_split = self._import_and_cache('train_test_split')
        mean_squared_error = self._import_and_cache('mean_squared_error')

        # Find and load model.
        model = self._find_and_load_model(target_column_name)

        # Split dataset into feature and target DataFrames for train model training.
        features = input_dataset[input_column_names]
        targets = input_dataset[target_column_name].values.ravel()

        # Split the data into training and testing sets.
        x_train, x_test, y_train, y_test = train_test_split(
            features,
            targets,
            test_size=1 - train_test_ratio,
            random_state=42)

        # Determine if the model can continue training.
        if hasattr(model, 'partial_fit'):
            # Continue training the model using partial_fit as it appears available.
            model.partial_fit(x_train, y_train)
            retraining_or_optimising = "continued training"
        else:
            # Perform hyperparameter optimization again if partial_fit is not available (aka retrain).
            model, test_mse, test_r2 = self._optimise_model(
                model, input_dataset, input_column_names, target_column_name, train_test_ratio)
            retraining_or_optimising = "retraining with hyperparameter optimisation"

        # Evaluate the model on the test data.
        test_predictions = model.predict(x_test)
        test_mse = mean_squared_error(y_test, test_predictions)
        test_r2 = r2_score(y_test, test_predictions)

        print(f"After further optimising via {retraining_or_optimising}:\n"
              f"Test MSE = {test_mse:.4f}, Test R² = {test_r2:.4f} - {type(model).__name__}")

        # Save the model.
        model_directory = './models'
        model_save_path = f'{model_directory}/model_{target_column_name}.pkl'
        os.makedirs(model_directory, exist_ok=True)
        joblib.dump(model, model_save_path)

        print(f"Model {target_column_name} saved to {model_save_path}")

    def _optimise_model(self, model, input_dataset, input_column_names, target_column_name, ratio):
        """
        Optimise provided model's hyperparameters to improve performance.
        Why: Allows for further performance gains from

        Parameters
        ----------
        model : The provided model to optimise.
        input_dataset : Input data to use as for model training.
        input_column_names : Names of columns we want to use as input to predict values with.
        target_column_name : Name of column we want to train our model to predict the values of.
        ratio : The ratio of Training + Validation to Testing data.

        Returns
        -------
        best_model_version : The most performant model after hyperparameter optimisation.
        test_mse : Mean Squared Error of the optimised model when evaluated against unseen test data.
        test_r2 : R² score of the optimised model when evaluated against unseen test data.
        """

        # Load relevant libraries, if not already cached.
        r2_score = self._import_and_cache('r2_score')
        train_test_split = self._import_and_cache('train_test_split')
        mean_squared_error = self._import_and_cache('mean_squared_error')
        randomised_search_cv = self._import_and_cache('RandomizedSearchCV')

        # Split the dataset into feature and target columns for single-objective model training.
        targets, features = self._find_model_targets_and_features(input_dataset, input_column_names, target_column_name)

        # Split the data into training and testing sets to allow for accurate future model performance evaluation.
        x_train, x_test, y_train, y_test = train_test_split(features, targets, test_size=1 - ratio, random_state=42)

        # Define the model's name for accessing in param grids.
        model_name = type(model).__name__.replace("Regressor", "").replace("SVR", "Support Vector Machine")

        # Load model types and some of their hyperparameters for initial processing.
        _, comprehensive_param_grids = self._load_parameter_grids()
        if model_name not in comprehensive_param_grids:
            raise ValueError(f"Unsupported model type: {model_name}")
        param_grid = comprehensive_param_grids[model_name]

        # Use RandomizedSearchCV for hyperparameter optimization.
        random_search = randomised_search_cv(
            model,
            param_distributions=param_grid,
            n_iter=10,
            cv=5,
            scoring='neg_mean_squared_error',
            n_jobs=-1,
            random_state=42,
            verbose=0
        )
        random_search.fit(x_train, y_train)

        # Get the best model from the random search.
        best_model_version = random_search.best_estimator_

        # Evaluate the optimised model.
        test_predictions = best_model_version.predict(x_test)
        test_mse = mean_squared_error(y_test, test_predictions)
        test_r2 = r2_score(y_test, test_predictions)

        return best_model_version, test_mse, test_r2

    """ Static Methods """

    @staticmethod
    def _import_and_cache(module_name: str):
        """
        Import a module or function if it's not already in the global scope for more performant function calls.
        Why: Dynamic library loading helps perf., while caching avoids python memory assignment issues with high usage.

         Parameters
        ----------
        module_name : The name of the module to import.

        Returns
        -------
        module : The imported module.
        """

        # Check if module already has been imported.
        if module_name in globals():
            return globals()[module_name]

        # Find and import relevant module.
        module = None
        match module_name:
            case 'SVR':
                from sklearn.svm import SVR
                module = SVR
            case 'r2_score':
                from sklearn.metrics import r2_score
                module = r2_score
            case 'mean_squared_error':
                from sklearn.metrics import mean_squared_error
                module = mean_squared_error
            case 'DecisionTreeRegressor':
                from sklearn.tree import DecisionTreeRegressor
                module = DecisionTreeRegressor
            case 'GridSearchCV':
                from sklearn.model_selection import GridSearchCV
                module = GridSearchCV
            case 'KNeighborsRegressor':
                from sklearn.neighbors import KNeighborsRegressor
                module = KNeighborsRegressor
            case 'LinearRegression':
                from sklearn.linear_model import LinearRegression
                module = LinearRegression
            case 'RandomForestRegressor':
                from sklearn.ensemble import RandomForestRegressor
                module = RandomForestRegressor
            case 'train_test_split':
                from sklearn.model_selection import train_test_split
                module = train_test_split
            case 'RandomizedSearchCV':
                from sklearn.model_selection import RandomizedSearchCV
                module = RandomizedSearchCV
        globals()[module_name] = module

        return module

    @staticmethod
    def _load_parameter_grids() -> tuple[dict, dict]:
        """
        Serves as a single source of model types and parameters for inter-function consistency.
        Why: Avoids discrepancies between model properties between functions.

        Returns
        -------
        shallow_param_grids : Model types, alongside a few of their hyperparameters.
        comprehensive_param_grids : Models types, alongside a more comprehensive list of their hyperparameters.
        """

        # Define models and hyperparameters for quick initial / general testing.
        shallow_param_grids = {
            'Linear Regression': {
                # No hyperparameters exist for linear regression.
            },
            'K-Nearest Neighbors': {
                'n_neighbors': [3, 5, 7]
            },
            'Support Vector Machine': {
                'C': [0.1, 1, 10],
                'kernel': ['linear', 'rbf']
            },
            'Decision Tree': {
                'max_depth': [None, 10, 20]
            },
            'RandomForest': {
                'n_estimators': [50, 100, 150],
                'max_depth': [None, 10, 20]
            }
        }

        # Define a large hyperparameter space for optimization.
        comprehensive_param_grids = {
            'Linear Regression': {
                # Linear regression is just linear regression so there is nothing to tune but adding
                # for consistency.
            },
            'RandomForest': {
                'n_estimators': randint(50, 500),
                'max_depth': [None] + list(range(10, 51, 5)),
                'min_samples_split': randint(2, 11),
                'min_samples_leaf': randint(1, 5),
                'max_features': ['sqrt', 'log2', None]
            },
            'Decision Tree': {
                'max_depth': [None] + list(range(10, 51, 5)),
                'min_samples_split': randint(2, 11),
                'min_samples_leaf': randint(1, 5),
                'max_features': ['sqrt', 'log2', None]
            },
            'K-Nearest Neighbors': {
                'n_neighbors': randint(1, 20),
                'weights': ['uniform', 'distance'],
                'algorithm': ['auto', 'ball_tree', 'kd_tree', 'brute'],
                'leaf_size': randint(20, 50)
            },
            'Support Vector Machine': {
                'C': uniform(0.1, 100),
                'kernel': ['linear', 'rbf', 'poly', 'sigmoid'],
                'gamma': ['scale', 'auto'] + list(arange(0.001, 0.1, 0.001)),
                'degree': randint(2, 6)
            }
        }

        return shallow_param_grids, comprehensive_param_grids

    @staticmethod
    def _find_and_load_model(target_column_name: str):
        """
        Find and load the model for the specified target name, checking all subdirectories on script's execution path.
        Why: Allows for quick finding of models without the hassle of specifying a path.

        Parameters
        ----------
        target_column_name : Name of target of prediction. (e.g. eta_is, phi_op, etc.)

        Returns
        -------
        model : The loaded model.
        """

        # Find model (if possible).
        model_path = None
        if os.path.exists(f"./models/model_{target_column_name}.pkl"):
            model_path = f"./models/model_{target_column_name}.pkl"
        elif os.path.exists(f"./model_{target_column_name}.pkl"):
            model_path = f"./model_{target_column_name}.pkl"
        else:
            # Recursively search for the model in all subdirectories.
            # This shouldn't take too long so long as the script execution folder isn't a clusterfuck of folders...
            for root, _, files in os.walk("."):
                if f"model_{target_column_name}.pkl" in files:
                    model_path = os.path.join(root, f"model_{target_column_name}.pkl")
                    break

        # Load model.
        if model_path:
            model = joblib.load(model_path)
        else:
            # Make directory such that when user is alerted to model missing, a prepared path for where to put it exists
            # for them to throw the model into if they find it.
            os.makedirs("./models/", exist_ok=True)
            error_message = (f"ModelSearchError:\nModel file for target ‘{target_column_name}’ not found locally."
                             f"\nThis function checks all folders within the folder it executes from to find the model."
                             f"\nThe function was executed from the folder: {os.getcwd()}"
                             f"\nThus, ensure the ‘model_{target_column_name}.pkl’ is located on the the above path."
                             f"\nIdeally, place it inside the /models/ folder found at {os.getcwd()} for quick access.")
            raise FileNotFoundError(error_message)

        return model

    @staticmethod
    def _find_model_targets_and_features(dataset: DataFrame, input_column_names: list,
                                         target_column_name: str) -> tuple[DataFrame, DataFrame]:
        """
        Find and load the model for the specified target name, checking all subdirectories on script's execution path.
        Why: Allows for quick finding of models without the hassle of specifying a path.

        Parameters
        ----------
        dataset : Input data to use as model input.
        input_column_names : Names of columns we want to use as input to predict values with.
        target_column_name : Name of column we want to train our model to predict the values of.

        Returns
        -------
        targets : A DataFrame of training targets, and nothing else.
        features : A DataFrame of training features, and nothing else.
        """

        # Ensure dataset contains only relevant columns to avoid errors from unexpected columns being present.
        relevant_columns = input_column_names + [target_column_name]
        dataset = dataset[relevant_columns]

        # Split into features and target datasets to train models.
        features = dataset.drop(columns=[target_column_name])
        targets = dataset[[target_column_name]].values.ravel()

        return targets, features
