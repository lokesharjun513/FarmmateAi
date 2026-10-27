enum CropCreationOutcome {
  none,
  planReady,
  planFailed;

  bool get cropWasSaved => this != CropCreationOutcome.none;
}
