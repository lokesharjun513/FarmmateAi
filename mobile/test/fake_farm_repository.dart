import 'package:mobile/features/farm/data/farm_repository.dart';
import 'package:mobile/features/farm/data/models/farm_model.dart';

class FakeFarmRepository implements FarmRepository {
  final List<FarmModel> _farms;

  FakeFarmRepository({List<FarmModel>? farms})
      : _farms = farms ?? [
          const FarmModel(
            id: '1',
            farmerId: 'f1',
            farmName: 'Test Farm 1',
            state: 'State',
            district: 'District',
            mandal: 'Mandal',
            village: 'Village',
            latitude: 10.0,
            longitude: 20.0,
            landArea: 10.0,
            landUnit: 'Acres',
            soilType: 'Loam',
            waterSource: 'Well',
            waterAvailability: 'Good',
            irrigationMethod: 'Drip',
            isPrimary: true,
          ),
        ];

  @override
  Future<List<FarmModel>> getFarms() async {
    return _farms;
  }

  @override
  Future<FarmModel> createFarm(FarmCreateInput input) async {
    throw UnimplementedError();
  }

  @override
  Future<FarmModel> setPrimary(String farmId) async {
    throw UnimplementedError();
  }
}
